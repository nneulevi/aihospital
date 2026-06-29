"""Optional MONAI-based training components for hemorrhage classification.

This module is intentionally optional. The lightweight PyTorch pipeline remains
the default so the project can run without MONAI installed. Install MONAI and
use ``train_monai.py`` when you want the more standardized medical imaging
pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

try:
    from .config import INPUT_SHAPE, WINDOW_MAX, WINDOW_MIN
    from .dataset import HemorrhageRecord
except ImportError:  # pragma: no cover - direct script fallback.
    from config import INPUT_SHAPE, WINDOW_MAX, WINDOW_MIN
    from dataset import HemorrhageRecord


def require_monai():
    try:
        import monai  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent.
        raise RuntimeError(
            "MONAI is not installed. Install it with `pip install monai` "
            "or use the default train.py pipeline."
        ) from exc
    return monai


def records_to_monai_items(records: list[HemorrhageRecord]) -> list[dict[str, Any]]:
    return [
        {
            "image": str(record.image_path),
            "label": np.asarray([float(record.label)], dtype=np.float32),
            "case_id": record.case_id,
        }
        for record in records
    ]


def build_transforms(
    *,
    target_shape: tuple[int, int, int] = INPUT_SHAPE,
    window_min: float = WINDOW_MIN,
    window_max: float = WINDOW_MAX,
    training: bool = False,
):
    require_monai()
    from monai.transforms import (  # type: ignore
        Compose,
        EnsureChannelFirstd,
        EnsureTyped,
        LoadImaged,
        RandFlipd,
        RandGaussianNoised,
        RandRotate90d,
        Resized,
        ScaleIntensityRanged,
    )

    transforms = [
        LoadImaged(keys=["image"], image_only=True),
        EnsureChannelFirstd(keys=["image"]),
        ScaleIntensityRanged(
            keys=["image"],
            a_min=window_min,
            a_max=window_max,
            b_min=0.0,
            b_max=1.0,
            clip=True,
        ),
        Resized(keys=["image"], spatial_size=target_shape, mode="trilinear"),
    ]
    if training:
        transforms.extend(
            [
                RandFlipd(keys=["image"], prob=0.5, spatial_axis=0),
                RandFlipd(keys=["image"], prob=0.5, spatial_axis=1),
                RandRotate90d(keys=["image"], prob=0.25, max_k=3),
                RandGaussianNoised(keys=["image"], prob=0.15, mean=0.0, std=0.01),
            ]
        )
    transforms.append(EnsureTyped(keys=["image", "label"], dtype=torch.float32))
    return Compose(transforms)


def build_monai_dataset(records: list[HemorrhageRecord], target_shape: tuple[int, int, int], training: bool, cache_rate: float = 0.0):
    require_monai()
    from monai.data import CacheDataset, Dataset  # type: ignore

    items = records_to_monai_items(records)
    transforms = build_transforms(target_shape=target_shape, training=training)
    if cache_rate > 0:
        return CacheDataset(data=items, transform=transforms, cache_rate=cache_rate)
    return Dataset(data=items, transform=transforms)


def build_monai_classifier(network: str = "densenet121"):
    require_monai()
    if network == "densenet121":
        from monai.networks.nets import DenseNet121  # type: ignore

        return DenseNet121(spatial_dims=3, in_channels=1, out_channels=1)
    if network == "densenet169":
        from monai.networks.nets import DenseNet169  # type: ignore

        return DenseNet169(spatial_dims=3, in_channels=1, out_channels=1)
    raise ValueError(f"unsupported MONAI network: {network}")
