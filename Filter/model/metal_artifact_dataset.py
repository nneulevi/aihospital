"""Dataset utilities for training 3D U-Net on generated metal artifact masks."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import torch
from torch import Tensor
from torch.utils.data import Dataset

try:
    import SimpleITK as sitk
except ImportError as exc:  # pragma: no cover - dependency guard.
    raise SystemExit("SimpleITK is required. Install it with: pip install SimpleITK") from exc


@dataclass(frozen=True)
class ArtifactRecord:
    ct_path: Path
    mask_path: Path
    stats_path: Optional[Path]
    case_id: str


def _is_supported_volume(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith((".nii", ".nii.gz", ".nrrd", ".mha", ".mhd"))


def load_directory_records(ct_dir: Path, mask_dir: Path) -> list[ArtifactRecord]:
    """Load paired CT/mask records from two directories.

    Files are paired by exact file name. For example:
    ``datasets/CT/000_CT.nii.gz`` is matched with
    ``datasets/mask/000_CT.nii.gz``.
    """

    ct_dir = ct_dir.resolve()
    mask_dir = mask_dir.resolve()
    if not ct_dir.exists():
        raise ValueError(f"CT directory not found: {ct_dir}")
    if not mask_dir.exists():
        raise ValueError(f"mask directory not found: {mask_dir}")

    mask_by_name = {path.name: path for path in mask_dir.iterdir() if path.is_file() and _is_supported_volume(path)}
    records: list[ArtifactRecord] = []
    missing_masks: list[str] = []
    for ct_path in sorted(path for path in ct_dir.iterdir() if path.is_file() and _is_supported_volume(path)):
        mask_path = mask_by_name.get(ct_path.name)
        if mask_path is None:
            missing_masks.append(ct_path.name)
            continue
        records.append(
            ArtifactRecord(
                ct_path=ct_path,
                mask_path=mask_path,
                stats_path=None,
                case_id=ct_path.name,
            )
        )

    if missing_masks:
        preview = ", ".join(missing_masks[:5])
        raise ValueError(f"Missing {len(missing_masks)} mask files for CT files: {preview}")
    if not records:
        raise ValueError(f"No paired CT/mask volumes found in {ct_dir} and {mask_dir}")
    return records


def load_records(manifest_path: Path) -> list[ArtifactRecord]:
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records: list[ArtifactRecord] = []
    for index, item in enumerate(manifest.get("items", [])):
        outputs = item.get("outputs", {})
        ct_path = Path(outputs.get("ct_volume_nii", ""))
        mask_path = Path(outputs.get("metal_mask_nii", ""))
        stats_path = Path(outputs["stats"]) if outputs.get("stats") else None
        if not ct_path.exists() or not mask_path.exists():
            continue
        case_id = Path(item.get("input_folder", f"case_{index}")).parts[-3] if item.get("input_folder") else f"case_{index}"
        records.append(ArtifactRecord(ct_path=ct_path, mask_path=mask_path, stats_path=stats_path, case_id=case_id))
    if not records:
        raise ValueError(f"No usable ct/mask pairs found in {manifest_path}")
    return records


def split_records(
    records: Sequence[ArtifactRecord],
    val_fraction: float,
    seed: int,
) -> tuple[list[ArtifactRecord], list[ArtifactRecord]]:
    if not 0.0 <= val_fraction < 1.0:
        raise ValueError("val_fraction must be in [0, 1)")
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    val_count = max(1, round(len(shuffled) * val_fraction)) if len(shuffled) > 1 and val_fraction > 0 else 0
    val_records = shuffled[:val_count]
    train_records = shuffled[val_count:]
    if not train_records:
        train_records, val_records = shuffled, []
    return train_records, val_records


def read_nifti(path: Path) -> np.ndarray:
    array = sitk.GetArrayFromImage(sitk.ReadImage(str(path)))
    if array.ndim != 3:
        raise ValueError(f"Expected 3D volume: {path}, got shape={array.shape}")
    return array


def normalize_ct(volume: np.ndarray, window: tuple[float, float]) -> np.ndarray:
    lo, hi = window
    if hi <= lo:
        raise ValueError("window high must be greater than window low")
    volume = np.clip(volume.astype(np.float32, copy=False), lo, hi)
    volume = (volume - lo) / (hi - lo)
    return volume * 2.0 - 1.0


class MetalArtifactPatchDataset(Dataset[tuple[Tensor, Tensor]]):
    """Deterministic 3D patch dataset.

    A fixed patch plan is generated from ``seed`` and ``length``. Each item then
    reads a CT/mask pair, samples either a positive-centered or random crop, and
    returns tensors shaped ``(1, D, H, W)``.
    """

    def __init__(
        self,
        records: Sequence[ArtifactRecord],
        patch_size: tuple[int, int, int] = (32, 128, 128),
        length: Optional[int] = None,
        positive_fraction: float = 0.7,
        seed: int = 2026,
        window: tuple[float, float] = (-1000.0, 3000.0),
        max_cache_items: int = 2,
        augment: bool = False,
        record_weights: Optional[Sequence[float]] = None,
    ) -> None:
        if not records:
            raise ValueError("records must not be empty")
        if any(size <= 0 for size in patch_size):
            raise ValueError("patch_size must contain positive integers")
        if not 0.0 <= positive_fraction <= 1.0:
            raise ValueError("positive_fraction must be in [0, 1]")
        self.records = list(records)
        self.patch_size = tuple(int(v) for v in patch_size)
        self.length = int(length) if length is not None else len(self.records)
        self.positive_fraction = float(positive_fraction)
        self.seed = int(seed)
        self.window = window
        self.max_cache_items = int(max_cache_items)
        self.augment = bool(augment)
        self.record_weights = self._normalize_record_weights(record_weights)
        self._cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        self._cache_order: list[int] = []
        self.epoch = 0
        self.patch_plan: list[tuple[int, bool, int]] = []
        self.set_epoch(0)

    def set_epoch(self, epoch: int) -> None:
        self.epoch = int(epoch)
        rng = np.random.default_rng(self.seed + self.epoch * 100_003)
        self.patch_plan = []
        for _ in range(self.length):
            record_index = int(rng.choice(len(self.records), p=self.record_weights))
            prefer_positive = bool(rng.random() < self.positive_fraction)
            item_seed = int(rng.integers(0, np.iinfo(np.int32).max))
            self.patch_plan.append((record_index, prefer_positive, item_seed))

    def _normalize_record_weights(self, weights: Optional[Sequence[float]]) -> Optional[np.ndarray]:
        if weights is None:
            return None
        array = np.asarray(weights, dtype=np.float64)
        if array.shape != (len(self.records),):
            raise ValueError("record_weights length must match records length")
        array = np.maximum(array, 0.0)
        total = float(array.sum())
        if total <= 0:
            return None
        return array / total

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        record_index, prefer_positive, item_seed = self.patch_plan[index]
        volume, mask = self._load_pair(record_index)
        rng = np.random.default_rng(item_seed)
        volume_patch, mask_patch = self._sample_patch(volume, mask, prefer_positive, rng)
        if self.augment:
            volume_patch, mask_patch = self._augment_patch(volume_patch, mask_patch, rng)

        volume_patch = normalize_ct(volume_patch, self.window)
        mask_patch = (mask_patch > 0).astype(np.float32, copy=False)
        return (
            torch.from_numpy(volume_patch[None, ...].copy()),
            torch.from_numpy(mask_patch[None, ...].copy()),
        )

    def _load_pair(self, record_index: int) -> tuple[np.ndarray, np.ndarray]:
        if record_index in self._cache:
            return self._cache[record_index]

        record = self.records[record_index]
        volume = read_nifti(record.ct_path).astype(np.float32, copy=False)
        mask = read_nifti(record.mask_path).astype(np.uint8, copy=False)
        if volume.shape != mask.shape:
            raise ValueError(
                f"CT/mask shape mismatch for {record.ct_path}: {volume.shape} vs {mask.shape}"
            )

        self._cache[record_index] = (volume, mask)
        self._cache_order.append(record_index)
        while len(self._cache_order) > self.max_cache_items:
            old_index = self._cache_order.pop(0)
            self._cache.pop(old_index, None)
        return volume, mask

    def _augment_patch(
        self,
        volume: np.ndarray,
        mask: np.ndarray,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray]:
        for axis in range(3):
            if rng.random() < 0.5:
                volume = np.flip(volume, axis=axis)
                mask = np.flip(mask, axis=axis)

        if volume.shape[1] == volume.shape[2] and rng.random() < 0.35:
            k = int(rng.integers(0, 4))
            volume = np.rot90(volume, k=k, axes=(1, 2))
            mask = np.rot90(mask, k=k, axes=(1, 2))

        if rng.random() < 0.35:
            scale = float(rng.uniform(0.9, 1.1))
            shift = float(rng.uniform(-50.0, 50.0))
            volume = volume * scale + shift

        if rng.random() < 0.25:
            noise_std = float(rng.uniform(5.0, 25.0))
            volume = volume + rng.normal(0.0, noise_std, size=volume.shape).astype(np.float32)

        return volume, mask

    def _sample_patch(
        self,
        volume: np.ndarray,
        mask: np.ndarray,
        prefer_positive: bool,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray]:
        padded_volume, padded_mask = self._pad_to_patch(volume, mask)
        spatial = np.array(padded_volume.shape, dtype=np.int64)
        patch = np.array(self.patch_size, dtype=np.int64)

        if prefer_positive and padded_mask.any():
            coords = np.argwhere(padded_mask > 0)
            center = coords[int(rng.integers(0, len(coords)))]
            starts = center - patch // 2
            max_starts = spatial - patch
            starts = np.minimum(np.maximum(starts, 0), max_starts)
        else:
            max_starts = spatial - patch
            starts = np.array(
                [int(rng.integers(0, max_start + 1)) if max_start > 0 else 0 for max_start in max_starts],
                dtype=np.int64,
            )

        z, y, x = starts.tolist()
        dz, dy, dx = self.patch_size
        crop = np.s_[z : z + dz, y : y + dy, x : x + dx]
        return padded_volume[crop], padded_mask[crop]

    def _pad_to_patch(self, volume: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        pads: list[tuple[int, int]] = []
        for size, target in zip(volume.shape, self.patch_size):
            total = max(0, target - int(size))
            before = total // 2
            pads.append((before, total - before))
        if any(before or after for before, after in pads):
            volume = np.pad(volume, pads, mode="edge")
            mask = np.pad(mask, pads, mode="constant", constant_values=0)
        return volume, mask


def compute_mask_balance(records: Sequence[ArtifactRecord]) -> tuple[int, int]:
    positive = 0
    total = 0
    for record in records:
        mask = read_nifti(record.mask_path)
        positive += int(np.count_nonzero(mask))
        total += int(mask.size)
    negative = max(total - positive, 0)
    return positive, negative


def compute_record_weights(records: Sequence[ArtifactRecord], empty_weight: float = 0.25) -> list[float]:
    """Weight cases by lesion presence so sparse positive volumes are sampled often enough."""

    weights: list[float] = []
    for record in records:
        positive = 0
        total = 0
        if record.stats_path and record.stats_path.exists():
            stats = json.loads(record.stats_path.read_text(encoding="utf-8"))
            positive = int(stats.get("stats", {}).get("final_voxels", 0))
            shape = stats.get("stats", {}).get("shape", [])
            if len(shape) == 3:
                total = int(shape[0]) * int(shape[1]) * int(shape[2])
        if total <= 0:
            mask = read_nifti(record.mask_path)
            positive = int(np.count_nonzero(mask))
            total = int(mask.size)

        if positive <= 0:
            weights.append(float(empty_weight))
        else:
            ratio = positive / max(total, 1)
            weights.append(1.0 + min(4.0, ratio * 100.0))
    return weights
