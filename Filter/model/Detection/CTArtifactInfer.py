"""AI inference wrapper for CT metal artifact segmentation.

The original Detection summary describes a 2D axial-slice U-Net. This
implementation keeps the same public methods but uses this project's 3D U-Net
checkpoint and sliding-window inference.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import torch

try:
    import SimpleITK as sitk
except ImportError as exc:  # pragma: no cover - dependency guard.
    raise SystemExit("SimpleITK is required. Install it with: pip install SimpleITK") from exc

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from config import DEFAULT_OVERLAP, DEFAULT_PATCH_SIZE, DEFAULT_THRESHOLD  # noqa: E402
from predict_unet3d import load_model, predict_volume  # noqa: E402
from Detection.Config import DEFAULT_WEIGHT_PATH, DEVICE  # noqa: E402


class CTArtifactInfer:
    """Load a 3D U-Net checkpoint and predict artifact masks."""

    def __init__(
        self,
        model_weight_path: Optional[str | os.PathLike[str]] = None,
        device: Optional[str] = None,
        patch_size: tuple[int, int, int] = DEFAULT_PATCH_SIZE,
        overlap: float = DEFAULT_OVERLAP,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self.device = torch.device(device or DEVICE)
        self.model_weight_path = Path(model_weight_path) if model_weight_path else DEFAULT_WEIGHT_PATH
        if not self.model_weight_path.exists():
            raise FileNotFoundError(
                f"Model checkpoint not found: {self.model_weight_path}. "
                "Train first with train_unet3d.py or pass model_weight_path explicitly."
            )
        self.patch_size = tuple(int(v) for v in patch_size)
        self.overlap = float(overlap)
        self.threshold = float(threshold)
        self.model = load_model(self.model_weight_path, self.device)

    def predict_slice(self, img_slice: np.ndarray) -> np.ndarray:
        """Predict one 2D axial slice by temporarily treating it as a 1-slice volume."""

        volume = img_slice.astype(np.float32, copy=False)[None, :, :]
        patch_size = (
            max(1, min(self.patch_size[0], 16)),
            self.patch_size[1],
            self.patch_size[2],
        )
        mask = predict_volume(
            self.model,
            volume,
            patch_size=patch_size,
            overlap=0.0,
            threshold=self.threshold,
            device=self.device,
        )
        return mask[0].astype(np.int16, copy=False)

    def predict_from_nii(self, nii_path: str | os.PathLike[str], save_mask_path: Optional[str | os.PathLike[str]] = None):
        sitk_ct = sitk.ReadImage(str(nii_path))
        return self.predict_from_sitk(sitk_ct, save_mask_path=save_mask_path)

    def predict_from_sitk(self, sitk_ct, save_mask_path: Optional[str | os.PathLike[str]] = None):
        volume = sitk.GetArrayFromImage(sitk_ct).astype(np.float32, copy=False)
        if volume.ndim == 2:
            volume = volume[None, :, :]
        if volume.ndim != 3:
            raise ValueError(f"Expected 2D/3D CT image, got shape={volume.shape}")
        mask = predict_volume(
            self.model,
            volume,
            patch_size=self.patch_size,
            overlap=self.overlap,
            threshold=self.threshold,
            device=self.device,
        )
        sitk_mask = sitk.GetImageFromArray(mask.astype(np.uint8, copy=False))
        sitk_mask.CopyInformation(sitk_ct)
        if save_mask_path is not None:
            save_path = Path(save_mask_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            sitk.WriteImage(sitk_mask, str(save_path))
        return sitk_mask

