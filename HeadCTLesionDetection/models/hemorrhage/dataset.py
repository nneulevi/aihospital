"""Dataset and preprocessing utilities for hemorrhage classification."""

from __future__ import annotations

import csv
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import SimpleITK as sitk
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset

try:
    from .config import INPUT_SHAPE, SUBTYPE_COLUMNS, WINDOW_MAX, WINDOW_MIN
except ImportError:  # pragma: no cover - direct script fallback.
    from config import INPUT_SHAPE, SUBTYPE_COLUMNS, WINDOW_MAX, WINDOW_MIN


@dataclass(frozen=True)
class HemorrhageRecord:
    case_id: str
    image_path: Path
    label: int
    split: str = "train"
    source: str = ""
    patient_id: str = ""
    study_id: str = ""
    series_id: str = ""


def _to_binary(value: object) -> int:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "positive", "pos"}:
        return 1
    if text in {"0", "false", "no", "n", "negative", "neg", ""}:
        return 0
    try:
        return 1 if float(text) > 0 else 0
    except ValueError:
        return 0


def infer_hemorrhage_label(row: dict[str, str]) -> int:
    if "hemorrhage" in row:
        return _to_binary(row.get("hemorrhage", "0"))
    return int(any(_to_binary(row.get(column, "0")) for column in SUBTYPE_COLUMNS))


def load_records(labels_csv: Path, image_root: Optional[Path] = None) -> list[HemorrhageRecord]:
    labels_csv = Path(labels_csv)
    image_root = image_root or labels_csv.parent
    if not labels_csv.exists():
        raise FileNotFoundError(f"labels.csv not found: {labels_csv}")

    records: list[HemorrhageRecord] = []
    with labels_csv.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        required = {"case_id", "image_path"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"labels.csv missing required columns: {sorted(missing)}")
        for row in reader:
            image_path = Path(row["image_path"])
            if not image_path.is_absolute():
                image_path = image_root / image_path
            records.append(
                HemorrhageRecord(
                    case_id=row["case_id"],
                    image_path=image_path,
                    label=infer_hemorrhage_label(row),
                    split=(row.get("split") or "train").strip().lower(),
                    source=row.get("source", ""),
                    patient_id=row.get("patient_id", ""),
                    study_id=row.get("study_id", ""),
                    series_id=row.get("series_id", ""),
                )
            )
    if not records:
        raise ValueError(f"labels.csv contains no records: {labels_csv}")
    return records


def split_records(records: list[HemorrhageRecord], split: str) -> list[HemorrhageRecord]:
    split = split.lower()
    return [record for record in records if record.split == split]


def split_train_val(records: list[HemorrhageRecord], val_fraction: float, seed: int) -> tuple[list[HemorrhageRecord], list[HemorrhageRecord]]:
    keyed: dict[str, list[HemorrhageRecord]] = {}
    for record in records:
        group_key = record.patient_id or record.study_id or record.case_id
        keyed.setdefault(group_key, []).append(record)
    keys = list(keyed)
    rng = random.Random(seed)
    rng.shuffle(keys)
    val_count = max(1, int(round(len(keys) * val_fraction))) if len(keys) > 1 else 0
    val_keys = set(keys[:val_count])
    train_records = [record for key in keys if key not in val_keys for record in keyed[key]]
    val_records = [record for key in keys if key in val_keys for record in keyed[key]]
    return train_records or records, val_records or train_records or records


def read_nifti_array(path: Path) -> np.ndarray:
    image = sitk.ReadImage(str(path))
    array = sitk.GetArrayFromImage(image).astype(np.float32, copy=False)
    if array.ndim == 2:
        array = array[None, :, :]
    if array.ndim != 3:
        raise ValueError(f"expected 2D/3D NIfTI image, got shape={array.shape}")
    return array


def window_normalize(volume: np.ndarray, window_min: float = WINDOW_MIN, window_max: float = WINDOW_MAX) -> np.ndarray:
    volume = np.clip(volume.astype(np.float32, copy=False), window_min, window_max)
    return (volume - window_min) / max(window_max - window_min, 1e-6)


def resize_volume(volume: np.ndarray, target_shape: tuple[int, int, int] = INPUT_SHAPE) -> np.ndarray:
    tensor = torch.from_numpy(volume[None, None, ...].copy()).float()
    resized = F.interpolate(tensor, size=target_shape, mode="trilinear", align_corners=False)
    return resized.numpy()[0, 0].astype(np.float32, copy=False)


def preprocess_nifti(
    path: Path,
    target_shape: tuple[int, int, int] = INPUT_SHAPE,
    window_min: float = WINDOW_MIN,
    window_max: float = WINDOW_MAX,
) -> torch.Tensor:
    volume = read_nifti_array(path)
    volume = window_normalize(volume, window_min, window_max)
    volume = resize_volume(volume, target_shape)
    return torch.from_numpy(volume[None, ...].copy()).float()


def cache_key_for_preprocess(
    path: Path,
    target_shape: tuple[int, int, int],
    window_min: float,
    window_max: float,
) -> str:
    resolved = path.resolve()
    stat = resolved.stat()
    raw = "|".join(
        [
            str(resolved),
            str(stat.st_size),
            str(stat.st_mtime_ns),
            ",".join(str(v) for v in target_shape),
            str(float(window_min)),
            str(float(window_max)),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def preprocess_nifti_cached(
    path: Path,
    target_shape: tuple[int, int, int],
    window_min: float,
    window_max: float,
    cache_dir: Optional[Path],
) -> torch.Tensor:
    if cache_dir is None:
        return preprocess_nifti(path, target_shape, window_min, window_max)

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{cache_key_for_preprocess(path, target_shape, window_min, window_max)}.pt"
    if cache_path.exists():
        try:
            return torch.load(cache_path, map_location="cpu", weights_only=True)
        except TypeError:
            return torch.load(cache_path, map_location="cpu")
        except Exception:
            cache_path.unlink(missing_ok=True)

    tensor = preprocess_nifti(path, target_shape, window_min, window_max)
    try:
        # Direct save is more reliable than atomic replace on some Windows
        # workspaces where torch's zip writer can keep a transient handle open.
        # If multiple workers race here, losing the cache write is harmless.
        torch.save(tensor, cache_path)
    except Exception:
        cache_path.unlink(missing_ok=True)
    return tensor


class HemorrhageDataset(Dataset):
    def __init__(
        self,
        records: list[HemorrhageRecord],
        target_shape: tuple[int, int, int] = INPUT_SHAPE,
        window_min: float = WINDOW_MIN,
        window_max: float = WINDOW_MAX,
        cache_dir: Optional[Path] = None,
    ) -> None:
        self.records = records
        self.target_shape = target_shape
        self.window_min = window_min
        self.window_max = window_max
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        record = self.records[index]
        image = preprocess_nifti_cached(
            record.image_path,
            self.target_shape,
            self.window_min,
            self.window_max,
            self.cache_dir,
        )
        label = torch.tensor([float(record.label)], dtype=torch.float32)
        return image, label
