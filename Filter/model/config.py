"""Central defaults for the 3D U-Net metal artifact project."""

from __future__ import annotations

import argparse
from pathlib import Path


MODEL_DIR = Path(__file__).resolve().parent
DATA_DIR = MODEL_DIR / "datasets"
CT_DIR = DATA_DIR / "CT"
MASK_DIR = DATA_DIR / "mask"
RUNS_DIR = MODEL_DIR / "runs"
DEFAULT_OUTPUT_DIR = RUNS_DIR / "metal_unet3d"

DEFAULT_EPOCHS = 5
DEFAULT_BATCH_SIZE = 1
DEFAULT_PATCH_SIZE = (32, 128, 128)
DEFAULT_TRAIN_PATCHES = 80
DEFAULT_VAL_PATCHES = 20
DEFAULT_POSITIVE_FRACTION = 0.7
DEFAULT_VAL_FRACTION = 0.2
DEFAULT_BASE_CHANNELS = 16
DEFAULT_DEPTH = 3
DEFAULT_LR = 1e-3
DEFAULT_WEIGHT_DECAY = 1e-4
DEFAULT_DICE_WEIGHT = 0.7
DEFAULT_BCE_WEIGHT = 0.3
DEFAULT_THRESHOLD = 0.35
DEFAULT_GRAD_CLIP = 1.0
DEFAULT_SEED = 2026
DEFAULT_NUM_WORKERS = 0
DEFAULT_MAX_POS_WEIGHT = 30.0
DEFAULT_OVERLAP = 0.5

CT_WINDOW = (-1000.0, 3000.0)


def parse_patch_size(text: str) -> tuple[int, int, int]:
    parts = [int(part.strip()) for part in text.lower().replace("x", ",").split(",") if part.strip()]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("patch size must look like 32,128,128")
    if any(part <= 0 for part in parts):
        raise argparse.ArgumentTypeError("patch size values must be positive")
    return tuple(parts)  # type: ignore[return-value]

