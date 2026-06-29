from __future__ import annotations

import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_ROOT = REPO_ROOT / "HeadCTLesionDetection" / "models" / "hemorrhage"
FILTER_ROOT = REPO_ROOT / "Filter"
for path in [REPO_ROOT, MODEL_ROOT]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from HeadCTLesionDetection.models.hemorrhage.config import INPUT_SHAPE
from HeadCTLesionDetection.models.hemorrhage.dataset import preprocess_nifti
from HeadCTLesionDetection.models.hemorrhage.infer import predict_hemorrhage
from HeadCTLesionDetection.models.hemorrhage.monai_pipeline import require_monai
from HeadCTLesionDetection.models.hemorrhage.model import Hemorrhage3DCNN


SAMPLE_CT = FILTER_ROOT / "model" / "runs" / "config_visual_smoke" / "sample_ct_positive.nii.gz"


def test_preprocess_nifti_shape() -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    tensor = preprocess_nifti(SAMPLE_CT, INPUT_SHAPE)
    assert tuple(tensor.shape) == (1, *INPUT_SHAPE)
    assert float(tensor.min()) >= 0.0
    assert float(tensor.max()) <= 1.0


def test_predict_hemorrhage_with_temporary_checkpoint(tmp_path: Path) -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    checkpoint = tmp_path / "best.pt"
    model = Hemorrhage3DCNN(base_channels=4, dropout=0.0)
    torch.save(
        {
            "model_state": model.state_dict(),
            "input_shape": INPUT_SHAPE,
            "base_channels": 4,
            "dropout": 0.0,
            "threshold": 0.5,
        },
        checkpoint,
    )
    result = predict_hemorrhage(SAMPLE_CT, checkpoint, device="cpu")
    assert result["lesion_type"] == "intracranial_hemorrhage"
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["detected"] in {True, False}
    assert "report_suggestion" in result


def test_monai_optional_dependency_message() -> None:
    try:
        require_monai()
    except RuntimeError as exc:
        assert "MONAI is not installed" in str(exc)
