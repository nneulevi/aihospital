"""2D axial-slice dataset built from paired 3D CT/mask NIfTI volumes."""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import torch
from torch import Tensor
from torch.utils.data import Dataset
import torch.nn.functional as F

try:
    import SimpleITK as sitk
except ImportError as exc:  # pragma: no cover - dependency guard.
    raise SystemExit("SimpleITK is required. Install it with: pip install SimpleITK") from exc

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from metal_artifact_dataset import ArtifactRecord, load_directory_records  # noqa: E402
from config_2d import WINDOW  # noqa: E402


@dataclass(frozen=True)
class SliceRecord:
    record_index: int
    slice_index: int
    has_positive: bool


def normalize_ct_slice(image: np.ndarray, window: tuple[float, float] = WINDOW) -> np.ndarray:
    lo, hi = window
    image = np.clip(image.astype(np.float32, copy=False), lo, hi)
    image = (image - lo) / max(hi - lo, 1e-6)
    return image * 2.0 - 1.0


def split_slice_records(
    slices: Sequence[SliceRecord],
    val_fraction: float,
    seed: int,
) -> tuple[list[SliceRecord], list[SliceRecord]]:
    shuffled = list(slices)
    random.Random(seed).shuffle(shuffled)
    val_count = max(1, round(len(shuffled) * val_fraction)) if len(shuffled) > 1 and val_fraction > 0 else 0
    return shuffled[val_count:], shuffled[:val_count]


class CTArtifactSliceDataset(Dataset[tuple[Tensor, Tensor]]):
    def __init__(
        self,
        records: Sequence[ArtifactRecord],
        slices: Sequence[SliceRecord],
        target_size: Optional[tuple[int, int]] = None,
        augment: bool = False,
        seed: int = 2026,
        max_cache_items: int = 16,
    ) -> None:
        if not records:
            raise ValueError("records must not be empty")
        if not slices:
            raise ValueError("slices must not be empty")
        self.records = list(records)
        self.slices = list(slices)
        self.target_size = target_size
        self.augment = bool(augment)
        self.seed = int(seed)
        self.max_cache_items = int(max_cache_items)
        self._cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        self._cache_order: list[int] = []

    def __len__(self) -> int:
        return len(self.slices)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        item = self.slices[index]
        volume, mask = self._load_pair(item.record_index)
        image = volume[item.slice_index]
        label = (mask[item.slice_index] > 0).astype(np.float32, copy=False)
        rng = np.random.default_rng(self.seed + index)
        if self.augment:
            image, label = self._augment(image, label, rng)
        image = normalize_ct_slice(image)
        image_tensor = torch.from_numpy(image[None, ...].copy()).float()
        label_tensor = torch.from_numpy(label[None, ...].copy()).float()
        if self.target_size is not None and tuple(image_tensor.shape[-2:]) != self.target_size:
            image_tensor = F.interpolate(image_tensor[None], size=self.target_size, mode="bilinear", align_corners=False)[0]
            label_tensor = F.interpolate(label_tensor[None], size=self.target_size, mode="nearest")[0]
        return image_tensor, label_tensor

    def _load_pair(self, record_index: int) -> tuple[np.ndarray, np.ndarray]:
        if record_index in self._cache:
            return self._cache[record_index]
        record = self.records[record_index]
        volume = sitk.GetArrayFromImage(sitk.ReadImage(str(record.ct_path))).astype(np.float32, copy=False)
        mask = sitk.GetArrayFromImage(sitk.ReadImage(str(record.mask_path))).astype(np.uint8, copy=False)
        if volume.shape != mask.shape:
            raise ValueError(f"shape mismatch: {record.ct_path} {volume.shape} vs {mask.shape}")
        self._cache[record_index] = (volume, mask)
        self._cache_order.append(record_index)
        while len(self._cache_order) > self.max_cache_items:
            old = self._cache_order.pop(0)
            self._cache.pop(old, None)
        return volume, mask

    def _augment(
        self,
        image: np.ndarray,
        label: np.ndarray,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray]:
        if rng.random() < 0.5:
            image = np.flip(image, axis=0)
            label = np.flip(label, axis=0)
        if rng.random() < 0.5:
            image = np.flip(image, axis=1)
            label = np.flip(label, axis=1)
        if image.shape[0] == image.shape[1] and rng.random() < 0.3:
            k = int(rng.integers(0, 4))
            image = np.rot90(image, k=k)
            label = np.rot90(label, k=k)
        if rng.random() < 0.25:
            image = image * float(rng.uniform(0.9, 1.1)) + float(rng.uniform(-40.0, 40.0))
        return image, label


def build_slice_index(records: Sequence[ArtifactRecord], keep_empty_fraction: float, seed: int) -> list[SliceRecord]:
    rng = random.Random(seed)
    items: list[SliceRecord] = []
    for record_index, record in enumerate(records):
        mask = sitk.GetArrayFromImage(sitk.ReadImage(str(record.mask_path)))
        for z in range(mask.shape[0]):
            has_positive = bool(np.any(mask[z] > 0))
            if has_positive or rng.random() < keep_empty_fraction:
                items.append(SliceRecord(record_index, z, has_positive))
    if not items:
        raise ValueError("No training slices selected")
    return items


def compute_slice_pixel_balance(
    records: Sequence[ArtifactRecord],
    slices: Sequence[SliceRecord],
    target_size: Optional[tuple[int, int]] = None,
) -> tuple[int, int]:
    """Compute positive/negative pixels from masks without loading CT volumes.

    This replaces the slow previous path that iterated through the full dataset
    and loaded both CT and mask for every selected slice.
    """

    positive = 0
    total = 0
    grouped: dict[int, list[int]] = {}
    for item in slices:
        grouped.setdefault(item.record_index, []).append(item.slice_index)

    for record_index, slice_indices in grouped.items():
        mask = sitk.GetArrayFromImage(sitk.ReadImage(str(records[record_index].mask_path)))
        for z in slice_indices:
            mask_slice = mask[z] > 0
            if target_size is None:
                positive += int(np.count_nonzero(mask_slice))
                total += int(mask_slice.size)
            else:
                # Nearest-neighbor resizing can change the exact count, but this
                # scaled estimate is sufficient for BCE pos_weight and is much faster.
                scale = (target_size[0] * target_size[1]) / max(mask_slice.size, 1)
                positive += int(round(np.count_nonzero(mask_slice) * scale))
                total += int(target_size[0] * target_size[1])

    negative = max(total - positive, 0)
    return positive, negative


def load_default_records(ct_dir: Path, mask_dir: Path) -> list[ArtifactRecord]:
    return load_directory_records(ct_dir, mask_dir)
