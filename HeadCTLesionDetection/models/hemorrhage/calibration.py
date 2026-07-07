"""Calibration helpers for hemorrhage model probabilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


DEFAULT_UNCERTAINTY_MARGIN = 0.05


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_probability_calibration(
    calibration_path: Optional[Path],
    *,
    default_threshold: float,
    default_margin: float = DEFAULT_UNCERTAINTY_MARGIN,
) -> dict[str, Any]:
    """Load threshold calibration from JSON, falling back to runtime defaults."""

    if not calibration_path or not Path(calibration_path).exists():
        return {
            "source": "runtime_default",
            "threshold": float(default_threshold),
            "uncertainty_margin": float(default_margin),
            "metrics": {},
            "path": None,
        }

    path = Path(calibration_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    threshold = payload.get("recommended_threshold")
    if threshold is None:
        threshold = (payload.get("best_f1") or {}).get("threshold")
    if threshold is None:
        threshold = (payload.get("calibration") or {}).get("best_f1_threshold")
    margin = payload.get("uncertainty_margin", default_margin)
    return {
        "source": str(payload.get("source") or "calibration_file"),
        "threshold": _as_float(threshold, default_threshold),
        "uncertainty_margin": _as_float(margin, default_margin),
        "metrics": payload.get("metrics") or {},
        "path": str(path),
    }


def confidence_band(probability: float, threshold: float, uncertainty_margin: float) -> str:
    margin = max(float(uncertainty_margin), 0.0)
    if probability >= threshold + margin:
        return "high_positive"
    if probability >= threshold:
        return "borderline_positive"
    if probability >= threshold - margin:
        return "borderline_negative"
    return "high_negative"


def calibrated_suggestion_prefix(band: str) -> str:
    if band == "high_positive":
        return "模型给出高置信阳性提示"
    if band == "borderline_positive":
        return "模型结果接近阈值但偏阳性"
    if band == "borderline_negative":
        return "模型结果接近阈值但偏阴性"
    return "模型给出低置信阴性提示"
