"""Configuration for the Head CT lesion detection service."""

from __future__ import annotations

import os
from pathlib import Path


def _float_list_env(name: str, default: str) -> list[float]:
    values = []
    for item in os.getenv(name, default).split(","):
        item = item.strip()
        if item:
            values.append(float(item))
    return values or [0.0]


SERVICE_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = Path(os.getenv("LESION_OUTPUT_ROOT", SERVICE_DIR / "lesion_outputs"))

API_PREFIX = "/api/head-ct-lesion"
MODULE_NAME = "head_ct_lesion_detection"
MODULE_VERSION = os.getenv("LESION_MODULE_VERSION", "v1.0.0")

HOST = os.getenv("LESION_HOST", "0.0.0.0")
PORT = int(os.getenv("LESION_PORT", "8020"))

DEFAULT_REQUESTED_LESIONS = os.getenv("LESION_REQUESTED_TYPES", "hemorrhage")
LESION_MODE = os.getenv("LESION_MODE", "mock").strip().lower()
HEMORRHAGE_CHECKPOINT = Path(
    os.getenv(
        "HEMORRHAGE_CHECKPOINT",
        SERVICE_DIR / "models" / "hemorrhage" / "runs" / "hemorrhage_v1" / "best.pt",
    )
)
HEMORRHAGE_DEVICE = os.getenv("HEMORRHAGE_DEVICE", "auto").strip().lower()
HEMORRHAGE_MODEL_PROVIDER = os.getenv("HEMORRHAGE_MODEL_PROVIDER", "local").strip().lower()
VINBIGDATA_CHECKPOINT = Path(os.getenv("VINBIGDATA_CHECKPOINT", str(HEMORRHAGE_CHECKPOINT)))
HEMORRHAGE_FALLBACK_CHECKPOINT = Path(os.getenv("HEMORRHAGE_FALLBACK_CHECKPOINT", str(HEMORRHAGE_CHECKPOINT)))
HEMORRHAGE_CHECKPOINT_PROVENANCE = os.getenv("HEMORRHAGE_CHECKPOINT_PROVENANCE", "unspecified").strip()
HEMORRHAGE_CHECKPOINT_FALLBACK_USED = os.getenv("HEMORRHAGE_CHECKPOINT_FALLBACK_USED", "false").strip().lower() == "true"
HEMORRHAGE_MATURE_CANDIDATE_PATHS = [
    item.strip()
    for item in os.getenv("HEMORRHAGE_MATURE_CANDIDATE_PATHS", "").split(";")
    if item.strip()
]
HEMORRHAGE_ALLOW_INFERENCE_FALLBACK = os.getenv("HEMORRHAGE_ALLOW_INFERENCE_FALLBACK", "true").strip().lower() == "true"
ICHSEG_CHECKPOINT = Path(
    os.getenv(
        "ICHSEG_CHECKPOINT",
        SERVICE_DIR / "models" / "hemorrhage" / "external_weights" / "ichseg_rank_nnunet" / "fold_0" / "checkpoint_final.pth",
    )
)
ICHSEG_PLANS = Path(
    os.getenv(
        "ICHSEG_PLANS",
        SERVICE_DIR / "models" / "hemorrhage" / "external_weights" / "ichseg_rank_nnunet" / "nnUNetPlans.json",
    )
)
ICHSEG_MANIFEST = Path(
    os.getenv(
        "ICHSEG_MANIFEST",
        SERVICE_DIR / "models" / "hemorrhage" / "external_weights" / "ichseg_rank_nnunet" / "manifest.json",
    )
)
ICHSEG_ENABLED = os.getenv("ICHSEG_ENABLED", "false").strip().lower() == "true"
ICHSEG_RUNTIME_STATUS = os.getenv(
    "ICHSEG_RUNTIME_STATUS",
    "enabled_executable" if ICHSEG_ENABLED else "checkpoint_registered_not_yet_executed_by_lesion_service",
).strip()
ICHSEG_INFERENCE_SHAPE = tuple(
    int(item.strip())
    for item in os.getenv("ICHSEG_INFERENCE_SHAPE", "16,192,192").split(",")
    if item.strip()
)
ICHSEG_THRESHOLD = float(os.getenv("ICHSEG_THRESHOLD", "0.5"))
VINBIGDATA_IMAGE_SIZE = int(os.getenv("VINBIGDATA_IMAGE_SIZE", "512"))
VINBIGDATA_MAX_SLICES = int(os.getenv("VINBIGDATA_MAX_SLICES", "64"))
VINBIGDATA_THRESHOLD = float(os.getenv("VINBIGDATA_THRESHOLD", "0.5"))
_VINBIGDATA_CALIBRATION_PATH = os.getenv("VINBIGDATA_CALIBRATION_PATH", "").strip()
VINBIGDATA_CALIBRATION_PATH = Path(_VINBIGDATA_CALIBRATION_PATH) if _VINBIGDATA_CALIBRATION_PATH else None
VINBIGDATA_SAMPLING_OFFSETS = _float_list_env("VINBIGDATA_SAMPLING_OFFSETS", "0")
VINBIGDATA_TTA_FLIP = os.getenv("VINBIGDATA_TTA_FLIP", "false").strip().lower() == "true"
MODEL_SUPPORTED_LESIONS = {"hemorrhage"}
SUPPORTED_LESIONS = {
    "hemorrhage": {
        "lesion_type": "intracranial_hemorrhage",
        "display_name": "颅内出血",
        "model_name": "mock_head_ct_hemorrhage_detector",
        "model_version": "mock-v1.0.0",
        "negative_suggestion": "未见明确颅内出血征象，建议医生结合原始影像复核。",
    },
    "fracture": {
        "lesion_type": "skull_fracture",
        "display_name": "颅骨骨折",
        "model_name": "mock_head_ct_fracture_detector",
        "model_version": "mock-v1.0.0",
        "negative_suggestion": "未见明确颅骨骨折征象，建议医生结合骨窗原始影像复核。",
    },
}
