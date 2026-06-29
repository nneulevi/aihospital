"""Default configuration for intracranial hemorrhage classification."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


MODEL_NAME = "head_ct_hemorrhage_classifier"
MODEL_VERSION = "v1.0.0"
LESION_TYPE = "intracranial_hemorrhage"
DISPLAY_NAME = "颅内出血"

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parents[1]
DATA_DIR = PROJECT_DIR / "datasets" / "hemorrhage"
LABELS_CSV = DATA_DIR / "labels.csv"
RUN_DIR = PACKAGE_DIR / "runs" / "hemorrhage_v1"

INPUT_SHAPE = (32, 160, 160)  # Z, H, W
WINDOW_MIN = -40.0
WINDOW_MAX = 120.0

BATCH_SIZE = 2
EPOCHS = 30
LR = 1e-4
WEIGHT_DECAY = 1e-4
NUM_WORKERS = 0
SEED = 42
THRESHOLD = 0.5
GRAD_ACCUM_STEPS = 1

LABEL_MAP = {"no_hemorrhage": 0, "hemorrhage": 1}
SUBTYPE_COLUMNS = [
    "epidural",
    "intraparenchymal",
    "intraventricular",
    "subarachnoid",
    "subdural",
]


def parse_shape(text: str | Iterable[int]) -> tuple[int, int, int]:
    if isinstance(text, str):
        parts = [int(part.strip()) for part in text.lower().replace("x", ",").split(",") if part.strip()]
    else:
        parts = [int(part) for part in text]
    if len(parts) != 3 or any(part <= 0 for part in parts):
        raise ValueError("shape must look like 32,160,160")
    return tuple(parts)  # type: ignore[return-value]
