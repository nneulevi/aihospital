"""Configuration for the Head CT lesion detection service."""

from __future__ import annotations

import os
from pathlib import Path


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
VINBIGDATA_IMAGE_SIZE = int(os.getenv("VINBIGDATA_IMAGE_SIZE", "512"))
VINBIGDATA_MAX_SLICES = int(os.getenv("VINBIGDATA_MAX_SLICES", "64"))
VINBIGDATA_THRESHOLD = float(os.getenv("VINBIGDATA_THRESHOLD", "0.5"))
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
