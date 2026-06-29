"""Default configuration for the standalone 2D U-Net方案."""

from __future__ import annotations

import argparse
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
MODEL_DIR = THIS_DIR.parents[0]
DATA_DIR = MODEL_DIR / "datasets"
CT_DIR = DATA_DIR / "CT"
MASK_DIR = DATA_DIR / "mask"
RUN_DIR = THIS_DIR / "runs" / "unet2d"

EPOCHS = 50
BATCH_SIZE = 4
LR = 1e-4
WEIGHT_DECAY = 1e-5
VAL_FRACTION = 0.2
SEED = 2026
NUM_WORKERS = 0
CACHE_ITEMS = 16
BASE_CHANNELS = 64
DICE_WEIGHT = 0.5
BCE_WEIGHT = 0.5
MAX_POS_WEIGHT = 20.0
THRESHOLD = 0.5
GRAD_CLIP = 1.0
ACCUM_STEPS = 1
WINDOW = (-1000.0, 3000.0)


def parse_size(text: str) -> tuple[int, int]:
    parts = [int(part.strip()) for part in text.lower().replace("x", ",").split(",") if part.strip()]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("size must look like 256,256")
    if any(part <= 0 for part in parts):
        raise argparse.ArgumentTypeError("size values must be positive")
    return tuple(parts)  # type: ignore[return-value]
