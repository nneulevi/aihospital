"""Detection GUI/runtime configuration."""

from __future__ import annotations

from pathlib import Path

import torch


MODEL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEIGHT_PATH = MODEL_ROOT / "runs" / "metal_unet3d" / "best_unet3d_metal.pt"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

