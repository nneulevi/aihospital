from __future__ import annotations

import json
import sys
import time
import pytest
from pathlib import Path

import torch
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
LESION_ROOT = REPO_ROOT / "HeadCTLesionDetection"
FILTER_ROOT = REPO_ROOT / "Filter"
for path in [REPO_ROOT, LESION_ROOT]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from HeadCTLesionDetection import LesionDetectionServer as lesion_server
from HeadCTLesionDetection.models.hemorrhage.config import INPUT_SHAPE
from HeadCTLesionDetection.models.hemorrhage.model import Hemorrhage3DCNN


app = lesion_server.app


SAMPLE_CT = FILTER_ROOT / "model" / "runs" / "config_visual_smoke" / "sample_ct_positive.nii.gz"


def write_temporary_checkpoint(path: Path) -> None:
    model = Hemorrhage3DCNN(base_channels=4, dropout=0.0)
    torch.save(
        {
            "model_state": model.state_dict(),
            "input_shape": INPUT_SHAPE,
            "base_channels": 4,
            "dropout": 0.0,
            "threshold": 0.5,
        },
        path,
    )


class ConstantVinBigDataModule(torch.nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        logits = x.new_full((x.size(0), x.size(1), 6), -4.0)
        logits[:, :, 0] = 2.0
        return logits


def write_temporary_vinbigdata_checkpoint(path: Path) -> None:
    module = torch.jit.trace(ConstantVinBigDataModule(), torch.zeros(1, 2, 3, 32, 32))
    module.save(str(path))


def wait_for_task(client: TestClient, task: dict) -> dict:
    current = task
    for _ in range(30):
        task_response = client.get(task["task_url"])
        assert task_response.status_code == 200
        current = task_response.json()
        if current["status"] in {"success", "failed"}:
            break
        time.sleep(0.1)
    return current


def test_lesion_health() -> None:
    lesion_server.LESION_MODE = "mock"
    with TestClient(app) as client:
        response = client.get("/api/head-ct-lesion/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["module"] == "head_ct_lesion_detection"
    assert payload["mode"] == "mock"
    assert "hemorrhage" in payload["supported_lesions"]
    assert "checkpoint_provenance" in payload["models"]["hemorrhage"]
    assert "checkpoint_fallback_used" in payload["models"]["hemorrhage"]


def test_lesion_mock_task_contract() -> None:
    lesion_server.LESION_MODE = "mock"
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    quality_context = {
        "artifact_detected": True,
        "severity": "moderate",
        "affected_slices": [1, 2],
        "artifact_reduction": {
            "enabled": True,
            "model_name": "InDuDoNet",
            "task_type": "metal_artifact_reduction",
            "correction_status": "checkpoint_registered_not_executable",
            "corrected_ct_url": None,
            "use_for_lesion_input": False,
            "warning": "已登记 InDuDoNet，但本次病灶识别仍使用原始 CT。",
        },
    }
    case_context = {"patient_id": "patient_001", "study_id": "study_001"}
    with TestClient(app) as client:
        with SAMPLE_CT.open("rb") as file_obj:
            response = client.post(
                "/api/head-ct-lesion/tasks",
                data={
                    "case_context": json.dumps(case_context),
                    "quality_context": json.dumps(quality_context),
                    "requested_lesions": "hemorrhage",
                },
                files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
            )
        assert response.status_code == 200
        task = response.json()
        assert task["status"] in {"queued", "running", "success"}

        current = wait_for_task(client, task)

        assert current["status"] == "success", current
        result_response = client.get(current["result_url"])
        assert result_response.status_code == 200
        result = result_response.json()
        assert result["module"] == "head_ct_lesion_detection"
        assert result["inference_mode"] == "mock"
        assert result["quality_context"]["severity"] == "moderate"
        assert result["input_policy"]["used_input"] == "original_ct"
        assert result["input_policy"]["artifact_reduction_status"] == "checkpoint_registered_not_executable"
        assert result["input_policy"]["corrected_ct_used"] is False
        assert result["results"][0]["lesion_type"] == "intracranial_hemorrhage"
        assert result["results"][0]["detected"] is False
        assert result["summary"]["detected_lesion_count"] == 0


def test_invalid_file_type_and_unsupported_lesion() -> None:
    lesion_server.LESION_MODE = "mock"
    with TestClient(app) as client:
        invalid_file = client.post(
            "/api/head-ct-lesion/tasks",
            files={"file": ("bad.txt", b"bad", "text/plain")},
        )
        assert invalid_file.status_code == 400
        assert invalid_file.json()["error_code"] == "INVALID_FILE_TYPE"

        unsupported = client.post(
            "/api/head-ct-lesion/tasks",
            data={"requested_lesions": "unknown"},
            files={"file": ("sample_ct_positive.nii.gz", b"fake", "application/octet-stream")},
        )
        assert unsupported.status_code == 400
        assert unsupported.json()["error_code"] == "UNSUPPORTED_LESION_TYPE"


def test_missing_task_and_result_errors() -> None:
    lesion_server.LESION_MODE = "mock"
    with TestClient(app) as client:
        task_response = client.get("/api/head-ct-lesion/tasks/not_existing_task")
        result_response = client.get("/api/head-ct-lesion/results/not_existing_task")
    assert task_response.status_code == 404
    assert task_response.json()["error_code"] == "TASK_NOT_FOUND"
    assert result_response.status_code == 404
    assert result_response.json()["error_code"] == "RESULT_NOT_FOUND"


def test_lesion_model_mode_uses_hemorrhage_checkpoint(tmp_path: Path) -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    checkpoint = tmp_path / "best.pt"
    write_temporary_checkpoint(checkpoint)
    original_mode = lesion_server.LESION_MODE
    original_checkpoint = lesion_server.HEMORRHAGE_CHECKPOINT
    original_device = lesion_server.HEMORRHAGE_DEVICE
    lesion_server.LESION_MODE = "model"
    lesion_server.HEMORRHAGE_CHECKPOINT = checkpoint
    lesion_server.HEMORRHAGE_DEVICE = "cpu"
    try:
        with TestClient(app) as client:
            health_response = client.get("/api/head-ct-lesion/health")
            assert health_response.status_code == 200
            health = health_response.json()
            assert health["mode"] == "model"
            assert health["models"]["hemorrhage"]["checkpoint_exists"] is True
            assert "fallback_checkpoint_exists" in health["models"]["hemorrhage"]

            with SAMPLE_CT.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-lesion/tasks",
                    data={"requested_lesions": "hemorrhage"},
                    files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
                )
            assert response.status_code == 200
            task = response.json()
            current = wait_for_task(client, task)
            assert current["status"] == "success", current

            result_response = client.get(current["result_url"])
            assert result_response.status_code == 200
            result = result_response.json()
            assert result["inference_mode"] == "model"
            assert result["results"][0]["lesion_type"] == "intracranial_hemorrhage"
            assert result["results"][0]["model_name"] == "head_ct_hemorrhage_classifier"
            assert 0.0 <= result["summary"]["highest_confidence"] <= 1.0
    finally:
        lesion_server.LESION_MODE = original_mode
        lesion_server.HEMORRHAGE_CHECKPOINT = original_checkpoint
        lesion_server.HEMORRHAGE_DEVICE = original_device


def test_lesion_model_mode_missing_checkpoint_marks_task_failed(tmp_path: Path) -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    original_mode = lesion_server.LESION_MODE
    original_checkpoint = lesion_server.HEMORRHAGE_CHECKPOINT
    lesion_server.LESION_MODE = "model"
    lesion_server.HEMORRHAGE_CHECKPOINT = tmp_path / "missing.pt"
    try:
        with TestClient(app) as client:
            health_response = client.get("/api/head-ct-lesion/health")
            assert health_response.status_code == 200
            assert health_response.json()["status"] == "degraded"

            with SAMPLE_CT.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-lesion/tasks",
                    data={"requested_lesions": "hemorrhage"},
                    files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
                )
            assert response.status_code == 200
            current = wait_for_task(client, response.json())
            assert current["status"] == "failed"
            assert current["error_code"] == "MODEL_CHECKPOINT_NOT_FOUND"
    finally:
        lesion_server.LESION_MODE = original_mode
        lesion_server.HEMORRHAGE_CHECKPOINT = original_checkpoint


def test_lesion_model_mode_uses_vinbigdata_provider(tmp_path: Path) -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    checkpoint = tmp_path / "vinbigdata_scripted.pt"
    write_temporary_vinbigdata_checkpoint(checkpoint)
    original_mode = lesion_server.LESION_MODE
    original_provider = lesion_server.HEMORRHAGE_MODEL_PROVIDER
    original_checkpoint = lesion_server.VINBIGDATA_CHECKPOINT
    original_device = lesion_server.HEMORRHAGE_DEVICE
    original_image_size = lesion_server.VINBIGDATA_IMAGE_SIZE
    original_max_slices = lesion_server.VINBIGDATA_MAX_SLICES
    lesion_server.LESION_MODE = "model"
    lesion_server.HEMORRHAGE_MODEL_PROVIDER = "vinbigdata"
    lesion_server.VINBIGDATA_CHECKPOINT = checkpoint
    lesion_server.HEMORRHAGE_DEVICE = "cpu"
    lesion_server.VINBIGDATA_IMAGE_SIZE = 32
    lesion_server.VINBIGDATA_MAX_SLICES = 2
    try:
        with TestClient(app) as client:
            health_response = client.get("/api/head-ct-lesion/health")
            assert health_response.status_code == 200
            health = health_response.json()
            assert health["mode"] == "model"
            assert health["model_provider"] == "vinbigdata"
            assert health["models"]["hemorrhage"]["checkpoint_exists"] is True

            with SAMPLE_CT.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-lesion/tasks",
                    data={"requested_lesions": "hemorrhage"},
                    files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
                )
            assert response.status_code == 200
            current = wait_for_task(client, response.json())
            assert current["status"] == "success", current

            result_response = client.get(current["result_url"])
            assert result_response.status_code == 200
            result = result_response.json()
            lesion = result["results"][0]
            assert lesion["provider"] == "vinbigdata"
            assert lesion["model_name"] == "vinbigdata_midl2020_cnn_lstm_ich"
            assert lesion["checkpoint_framework"] == "torchscript"
            assert lesion["detected"] is True
            assert lesion["subtype_probabilities"]["any"] > 0.8
    finally:
        lesion_server.LESION_MODE = original_mode
        lesion_server.HEMORRHAGE_MODEL_PROVIDER = original_provider
        lesion_server.VINBIGDATA_CHECKPOINT = original_checkpoint
        lesion_server.HEMORRHAGE_DEVICE = original_device
        lesion_server.VINBIGDATA_IMAGE_SIZE = original_image_size
        lesion_server.VINBIGDATA_MAX_SLICES = original_max_slices


def test_vinbigdata_raw_resnet_checkpoint_runs_without_local_fallback() -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    checkpoint = LESION_ROOT / "models" / "hemorrhage" / "external_weights" / "best_resnet50.pth"
    if not checkpoint.exists():
        pytest.skip(f"VinBigData raw checkpoint is not present: {checkpoint}")
    result = lesion_server.predict_vinbigdata_hemorrhage(
        SAMPLE_CT,
        checkpoint,
        device="cpu",
        quality_context={"severity": "mild"},
        threshold=0.5,
        image_size=64,
        max_slices=2,
    )
    assert result["provider"] == "vinbigdata"
    assert result["checkpoint_framework"] == "state_dict"
    assert "subtype_probabilities" in result
    assert set(result["subtype_probabilities"]).issuperset({"any", "subdural"})
    assert 0.0 <= result["subtype_probabilities"]["any"] <= 1.0


def test_ichseg_nnunet_segmentation_runtime_outputs_mask_and_preview() -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    checkpoint = LESION_ROOT / "models" / "hemorrhage" / "external_weights" / "ichseg_rank_nnunet" / "fold_0" / "checkpoint_final.pth"
    plans = LESION_ROOT / "models" / "hemorrhage" / "external_weights" / "ichseg_rank_nnunet" / "nnUNetPlans.json"
    classifier_checkpoint = LESION_ROOT / "models" / "hemorrhage" / "runs" / "hemorrhage_v1" / "smoke_best.pt"
    if not checkpoint.exists() or not plans.exists():
        pytest.skip(f"ICHSeg nnU-Net checkpoint is not present: {checkpoint}")
    original_values = {
        "LESION_MODE": lesion_server.LESION_MODE,
        "HEMORRHAGE_CHECKPOINT": lesion_server.HEMORRHAGE_CHECKPOINT,
        "HEMORRHAGE_DEVICE": lesion_server.HEMORRHAGE_DEVICE,
        "ICHSEG_ENABLED": lesion_server.ICHSEG_ENABLED,
        "ICHSEG_INFERENCE_SHAPE": lesion_server.ICHSEG_INFERENCE_SHAPE,
        "ICHSEG_THRESHOLD": lesion_server.ICHSEG_THRESHOLD,
    }
    lesion_server.LESION_MODE = "model"
    lesion_server.HEMORRHAGE_CHECKPOINT = classifier_checkpoint
    lesion_server.HEMORRHAGE_DEVICE = "cpu"
    lesion_server.ICHSEG_ENABLED = True
    lesion_server.ICHSEG_INFERENCE_SHAPE = (16, 128, 128)
    lesion_server.ICHSEG_THRESHOLD = 0.5
    try:
        with TestClient(app) as client:
            with SAMPLE_CT.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-lesion/tasks",
                    data={
                        "requested_lesions": "hemorrhage",
                        "quality_context": json.dumps({"severity": "mild"}, ensure_ascii=False),
                    },
                    files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
                )
            assert response.status_code == 200
            current = wait_for_task(client, response.json())
            assert current["status"] == "success", current
            result_response = client.get(current["result_url"])
            assert result_response.status_code == 200
            result = result_response.json()
            lesion = result["results"][0]
            assert lesion["task_type"] == "classification_plus_segmentation"
            assert lesion["mask_url"].endswith("/lesion_mask.nii.gz")
            assert lesion["preview_urls"]["axial"].endswith("/lesion_preview_axial.png")
            assert lesion["segmentation_runtime_status"] == "executed_direct_network_forward"
            assert lesion["segmentation_checkpoint_fallback_used"] is False
            assert lesion["segmentation_checkpoint_provenance"] == "mature_public_external"
            assert client.get(lesion["mask_url"]).status_code == 200
            assert client.get(lesion["preview_urls"]["axial"]).status_code == 200
    finally:
        for key, value in original_values.items():
            setattr(lesion_server, key, value)
