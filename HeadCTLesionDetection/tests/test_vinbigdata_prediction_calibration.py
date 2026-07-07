from __future__ import annotations

from HeadCTLesionDetection.models.hemorrhage.calibrate_predictions import calibrate_supervised, calibrate_unsupervised


def test_supervised_calibration_recommends_threshold_from_f1() -> None:
    rows = [
        {"case_id": "a", "label": 0, "positive_probability": 0.05},
        {"case_id": "b", "label": 0, "positive_probability": 0.20},
        {"case_id": "c", "label": 1, "positive_probability": 0.61},
        {"case_id": "d", "label": 1, "positive_probability": 0.91},
    ]

    calibration = calibrate_supervised(rows)

    assert calibration["source"] == "cq500ct200_supervised"
    assert calibration["recommended_threshold"] >= 0.21
    assert calibration["metrics"]["sensitivity"] == 1.0
    assert calibration["metrics"]["specificity"] == 1.0


def test_unsupervised_calibration_is_marked_as_distribution_only() -> None:
    rows = [
        {"case_id": "a", "positive_probability": 0.01},
        {"case_id": "b", "positive_probability": 0.10},
        {"case_id": "c", "positive_probability": 0.90},
    ]

    calibration = calibrate_unsupervised(rows, percentile=90)

    assert calibration["source"] == "cq500ct200_unsupervised_distribution"
    assert calibration["metrics"] == {}
    assert calibration["limitations"]
    assert calibration["recommended_threshold"] > 0.1
