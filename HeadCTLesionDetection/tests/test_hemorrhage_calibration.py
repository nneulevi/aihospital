from __future__ import annotations

import json
from pathlib import Path

from HeadCTLesionDetection.models.hemorrhage.infer import result_from_probability


def test_result_uses_calibrated_threshold_and_confidence_band(tmp_path: Path) -> None:
    calibration_path = tmp_path / "calibration.json"
    calibration_path.write_text(
        json.dumps(
            {
                "recommended_threshold": 0.37,
                "uncertainty_margin": 0.08,
                "source": "cq500ct200_supervised",
                "metrics": {"auc": 0.91, "sensitivity": 0.88, "specificity": 0.84},
            }
        ),
        encoding="utf-8",
    )

    result = result_from_probability(0.39, 0.5, calibration_path=calibration_path)

    assert result["detected"] is True
    assert result["decision_threshold"] == 0.37
    assert result["calibration"]["source"] == "cq500ct200_supervised"
    assert result["confidence_band"] == "borderline_positive"
    assert "接近阈值" in result["report_suggestion"]


def test_result_marks_high_confidence_positive_without_calibration_file() -> None:
    result = result_from_probability(0.91, 0.5)

    assert result["detected"] is True
    assert result["decision_threshold"] == 0.5
    assert result["confidence_band"] == "high_positive"
    assert result["calibration"]["source"] == "runtime_default"
