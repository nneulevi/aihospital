from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

FILTER_ROOT = Path(__file__).resolve().parents[2]
if str(FILTER_ROOT) not in sys.path:
    sys.path.insert(0, str(FILTER_ROOT))

from Fastapi import CTDetectionServer as server_3d
from Fastapi.CTDetectionServer import app as app_3d
from Fastapi.CTDetectionServer_unet2d import app as app_2d


SAMPLE_CT = FILTER_ROOT / "model" / "runs" / "config_visual_smoke" / "sample_ct_positive.nii.gz"


def test_health_contract() -> None:
    with TestClient(app_3d) as client:
        response = client.get("/api/ct-artifact/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["module"] == "ct_artifact_filter"
        assert payload["backend"] == "unet3d"
        assert "model_version" in payload
        assert "checkpoint_provenance" in payload["model"]
        assert "checkpoint_fallback_used" in payload["model"]
        assert "mature_mar_checkpoint_exists" in payload["model"]
        assert "mature_mar_task_type" in payload["model"]


def test_indudonet_registered_checkpoint_enables_local_mar_path() -> None:
    original_path = server_3d.MATURE_MAR_CHECKPOINT_PATH
    original_name = server_3d.MATURE_MAR_MODEL_NAME
    original_task_type = server_3d.MATURE_MAR_TASK_TYPE
    checkpoint = FILTER_ROOT / "model" / "external_weights" / "metal_artifact_reduction" / "InDuDoNet_latest.pt"
    try:
        server_3d.MATURE_MAR_CHECKPOINT_PATH = str(checkpoint)
        server_3d.MATURE_MAR_MODEL_NAME = "InDuDoNet"
        server_3d.MATURE_MAR_TASK_TYPE = "metal_artifact_reduction"
        status = server_3d.build_artifact_reduction_status()
        assert status["registered"] is True
        assert status["checkpoint_exists"] is True
        assert status["executable"] is True
        assert status["correction_status"] == "available_via_mask_guided_image_domain_mar"
        assert status["use_for_lesion_input"] is True
        assert status["execution_blockers"] == []
    finally:
        server_3d.MATURE_MAR_CHECKPOINT_PATH = original_path
        server_3d.MATURE_MAR_MODEL_NAME = original_name
        server_3d.MATURE_MAR_TASK_TYPE = original_task_type


def assert_detect_result_and_download_contract(app, expected_backend: str) -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    with TestClient(app) as client:
        with SAMPLE_CT.open("rb") as ct_file:
            response = client.post(
                "/api/ct-artifact/detect",
                files={"file": ("sample_ct_positive.nii.gz", ct_file, "application/octet-stream")},
            )
        assert response.status_code == 200
        payload = response.json()
        for key in [
            "request_id",
            "artifact_detected",
            "artifact_ratio",
            "severity",
            "affected_slices",
            "model_name",
            "model_version",
            "backend",
            "threshold",
            "elapsed_ms",
            "report_suggestion",
            "input_metadata",
            "download_url",
            "result_url",
            "preview_urls",
        ]:
            assert key in payload
        assert payload["artifact_segmentation"]["mask_url"] == payload["download_url"]
        assert payload["artifact_segmentation"]["severity"] == payload["severity"]
        assert payload["artifact_reduction"]["model_name"] in {"mask_guided_image_domain_mar", "InDuDoNet", None}
        assert payload["artifact_reduction"]["task_type"] in {"metal_artifact_reduction", None}
        assert payload["artifact_reduction"]["correction_status"] in {
            "not_configured",
            "checkpoint_registered_not_executable",
            "available_via_mask_guided_image_domain_mar",
            "executed",
            "corrected",
            "failed",
        }
        assert "use_for_lesion_input" in payload["artifact_reduction"]
        if payload["artifact_reduction"].get("corrected_ct_url"):
            corrected_response = client.get(payload["artifact_reduction"]["corrected_ct_url"])
            assert corrected_response.status_code == 200

        result_response = client.get(payload["result_url"])
        assert result_response.status_code == 200
        result_json = result_response.json()
        assert result_json["request_id"] == payload["request_id"]
        assert result_json["artifact_reduction"] == payload["artifact_reduction"]

        mask_response = client.get(payload["download_url"])
        assert mask_response.status_code == 200

        preview_response = client.get(payload["preview_urls"]["axial"])
        assert preview_response.status_code == 200
        assert preview_response.headers["content-type"].startswith("image/png")
        assert payload["backend"] == expected_backend


def test_detect_result_and_download_contract_3d() -> None:
    assert_detect_result_and_download_contract(app_3d, "unet3d")


def test_detect_result_and_download_contract_2d() -> None:
    assert_detect_result_and_download_contract(app_2d, "unet2d_axial_slices")


def assert_task_result_and_download_contract(app, expected_backend: str) -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    with TestClient(app) as client:
        with SAMPLE_CT.open("rb") as ct_file:
            response = client.post(
                "/api/ct-artifact/tasks",
                files={"file": ("sample_ct_positive.nii.gz", ct_file, "application/octet-stream")},
            )
        assert response.status_code == 200
        task = response.json()
        assert task["status"] in {"queued", "running", "success"}
        assert task["backend"] == expected_backend
        assert "task_id" in task
        assert "task_url" in task

        current = task
        for _ in range(30):
            task_response = client.get(task["task_url"])
            assert task_response.status_code == 200
            current = task_response.json()
            if current["status"] in {"success", "failed"}:
                break
            time.sleep(0.1)

        assert current["status"] == "success", current
        result_response = client.get(current["result_url"])
        assert result_response.status_code == 200
        result = result_response.json()
        assert result["request_id"] == task["task_id"]
        assert result["task_id"] == task["task_id"]
        assert result["backend"] == expected_backend

        mask_response = client.get(current["mask_url"])
        assert mask_response.status_code == 200

        preview_response = client.get(result["preview_urls"]["axial"])
        assert preview_response.status_code == 200
        assert preview_response.headers["content-type"].startswith("image/png")


def test_task_result_and_download_contract_3d() -> None:
    assert_task_result_and_download_contract(app_3d, "unet3d")


def test_task_result_and_download_contract_2d() -> None:
    assert_task_result_and_download_contract(app_2d, "unet2d_axial_slices")
