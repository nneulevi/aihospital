from __future__ import annotations

import sys
import time
import json
from pathlib import Path
from typing import Any, Optional

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
FILTER_ROOT = REPO_ROOT / "Filter"
ORCH_ROOT = REPO_ROOT / "HeadCTOrchestrator"
LESION_ROOT = REPO_ROOT / "HeadCTLesionDetection"
for path in [REPO_ROOT, FILTER_ROOT, ORCH_ROOT, LESION_ROOT]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from Fastapi.CTDetectionServer import app as filter_app  # noqa: E402
from HeadCTLesionDetection import LesionDetectionServer as lesion_srv  # noqa: E402
from HeadCTLesionDetection.LesionDetectionServer import app as lesion_app  # noqa: E402
from HeadCTLesionDetection.models.hemorrhage.create_smoke_checkpoint import create_smoke_checkpoint  # noqa: E402
from HeadCTOrchestrator import OrchestratorServer as orch  # noqa: E402
from HeadCTOrchestrator.ai_imaging_readiness import build_ai_imaging_status  # noqa: E402


SAMPLE_CT = FILTER_ROOT / "model" / "runs" / "config_visual_smoke" / "sample_ct_positive.nii.gz"


@pytest.fixture(autouse=True)
def disable_rag_for_pipeline_tests():
    old_rag_enabled = orch.RAG_ENABLED
    orch.RAG_ENABLED = False
    try:
        yield
    finally:
        orch.RAG_ENABLED = old_rag_enabled


class InProcessFilterClient:
    def absolute_url(self, url_or_path: Optional[str]) -> Optional[str]:
        if not url_or_path:
            return url_or_path
        if url_or_path.startswith(("http://", "https://")):
            return url_or_path
        return f"http://filter.local{url_or_path}"

    def health(self) -> dict[str, Any]:
        with TestClient(filter_app) as client:
            response = client.get("/api/ct-artifact/health")
            assert response.status_code == 200
            return response.json()

    def create_task(self, file_path: Path, filename: str, content_type: Optional[str]) -> dict[str, Any]:
        with TestClient(filter_app) as client:
            with file_path.open("rb") as file_obj:
                response = client.post(
                    "/api/ct-artifact/tasks",
                    files={"file": (filename, file_obj, content_type or "application/octet-stream")},
                )
            assert response.status_code == 200
            return response.json()

    def get_task(self, task_url: str) -> dict[str, Any]:
        path = task_url.replace("http://filter.local", "")
        with TestClient(filter_app) as client:
            response = client.get(path)
            assert response.status_code == 200
            return response.json()

    def get_result(self, result_url: str) -> dict[str, Any]:
        path = result_url.replace("http://filter.local", "")
        with TestClient(filter_app) as client:
            response = client.get(path)
            assert response.status_code == 200
            return response.json()


class UnavailableFilterClient:
    def absolute_url(self, url_or_path: Optional[str]) -> Optional[str]:
        return url_or_path

    def health(self) -> dict[str, Any]:
        raise ConnectionError("Filter service unavailable")

    def create_task(self, file_path: Path, filename: str, content_type: Optional[str]) -> dict[str, Any]:
        raise ConnectionError("Filter service unavailable")

    def get_task(self, task_url: str) -> dict[str, Any]:
        raise ConnectionError("Filter service unavailable")

    def get_result(self, result_url: str) -> dict[str, Any]:
        raise ConnectionError("Filter service unavailable")


class UnavailableLesionClient:
    def absolute_url(self, url_or_path: Optional[str]) -> Optional[str]:
        return url_or_path

    def health(self) -> dict[str, Any]:
        raise ConnectionError("Lesion service unavailable")

    def create_task(
        self,
        file_path: Path,
        filename: str,
        content_type: Optional[str],
        case_context: dict[str, Any],
        quality_context: dict[str, Any],
        requested_lesions: str,
    ) -> dict[str, Any]:
        raise ConnectionError("Lesion service unavailable")

    def get_task(self, task_url: str) -> dict[str, Any]:
        raise ConnectionError("Lesion service unavailable")

    def get_result(self, result_url: str) -> dict[str, Any]:
        raise ConnectionError("Lesion service unavailable")


class InProcessLesionClient:
    def absolute_url(self, url_or_path: Optional[str]) -> Optional[str]:
        if not url_or_path:
            return url_or_path
        if url_or_path.startswith(("http://", "https://")):
            return url_or_path
        return f"http://lesion.local{url_or_path}"

    def health(self) -> dict[str, Any]:
        with TestClient(lesion_app) as client:
            response = client.get("/api/head-ct-lesion/health")
            assert response.status_code == 200
            return response.json()

    def create_task(
        self,
        file_path: Path,
        filename: str,
        content_type: Optional[str],
        case_context: dict[str, Any],
        quality_context: dict[str, Any],
        requested_lesions: str,
    ) -> dict[str, Any]:
        with TestClient(lesion_app) as client:
            with file_path.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-lesion/tasks",
                    data={
                        "case_context": json.dumps(case_context, ensure_ascii=False),
                        "quality_context": json.dumps(quality_context, ensure_ascii=False),
                        "requested_lesions": requested_lesions,
                    },
                    files={"file": (filename, file_obj, content_type or "application/octet-stream")},
                )
            assert response.status_code == 200
            return response.json()

    def get_task(self, task_url: str) -> dict[str, Any]:
        path = task_url.replace("http://lesion.local", "")
        with TestClient(lesion_app) as client:
            response = client.get(path)
            assert response.status_code == 200
            return response.json()

    def get_result(self, result_url: str) -> dict[str, Any]:
        path = result_url.replace("http://lesion.local", "")
        with TestClient(lesion_app) as client:
            response = client.get(path)
            assert response.status_code == 200
            return response.json()


def test_orchestrator_health() -> None:
    orch.LESION_SERVICE_ENABLED = False
    orch.filter_client = InProcessFilterClient()
    with TestClient(orch.app) as client:
        response = client.get("/api/head-ct-ai/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["module"] == "head_ct_ai_orchestrator"
        assert payload["filter"]["status"] == "ok"


def test_orchestrator_pipeline_with_filter() -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    orch.LESION_SERVICE_ENABLED = False
    orch.filter_client = InProcessFilterClient()
    with TestClient(orch.app) as client:
        with SAMPLE_CT.open("rb") as file_obj:
            response = client.post(
                "/api/head-ct-ai/tasks",
                data={
                    "patient_id": "patient_001",
                    "study_id": "study_001",
                    "series_id": "series_001",
                    "report_id": "report_001",
                    "doctor_id": "doctor_001",
                },
                files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
            )
        assert response.status_code == 200
        task = response.json()
        assert task["status"] in {"queued", "running_filter", "success"}

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
        assert result["module"] == "head_ct_ai_orchestrator"
        assert result["task_id"] == task["task_id"]
        assert "quality_control" in result
        assert "lesion_analysis" in result
        assert "report_assist" in result
        assert result["case_context"]["patient_id"] == "patient_001"
        assert result["pipeline"]["quality_control"] == "success"
        assert result["pipeline"]["lesion_analysis"] == "not_configured"
        assert result["pipeline"]["report_assist"] == "success"
        assert isinstance(result["warnings"], list)
        assert "created_at" in result
        assert "finished_at" in result
        assert result["lesion_analysis"]["enabled"] is False
        assert result["lesion_analysis"]["status"] == "not_configured"
        assert result["report_assist"]["can_enter_report"] is False


def test_invalid_file_type_returns_stable_error() -> None:
    orch.LESION_SERVICE_ENABLED = False
    orch.filter_client = InProcessFilterClient()
    with TestClient(orch.app) as client:
        response = client.post(
            "/api/head-ct-ai/tasks",
            files={"file": ("not_ct.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 400
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["error_code"] == "INVALID_FILE_TYPE"


def test_missing_task_and_result_return_stable_errors() -> None:
    orch.LESION_SERVICE_ENABLED = False
    with TestClient(orch.app) as client:
        task_response = client.get("/api/head-ct-ai/tasks/not_existing_task")
        result_response = client.get("/api/head-ct-ai/results/not_existing_task")
    assert task_response.status_code == 404
    assert task_response.json()["error_code"] == "TASK_NOT_FOUND"
    assert result_response.status_code == 404
    assert result_response.json()["error_code"] == "RESULT_NOT_FOUND"


def test_filter_unavailable_marks_task_failed() -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    orch.LESION_SERVICE_ENABLED = False
    orch.filter_client = UnavailableFilterClient()
    with TestClient(orch.app) as client:
        health_response = client.get("/api/head-ct-ai/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "degraded"

        with SAMPLE_CT.open("rb") as file_obj:
            response = client.post(
                "/api/head-ct-ai/tasks",
                files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
            )
        assert response.status_code == 200
        task = response.json()

        task_response = client.get(task["task_url"])
        assert task_response.status_code == 200
        current = task_response.json()
        assert current["status"] == "failed"
        assert current["error_code"] == "FILTER_UNAVAILABLE"


def test_orchestrator_pipeline_with_mock_lesion_detection() -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    orch.LESION_SERVICE_ENABLED = True
    orch.LESION_REQUESTED_TYPES = "hemorrhage"
    orch.filter_client = InProcessFilterClient()
    orch.lesion_client = InProcessLesionClient()
    try:
        with TestClient(orch.app) as client:
            with SAMPLE_CT.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-ai/tasks",
                    data={"patient_id": "patient_lesion_001"},
                    files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
                )
            assert response.status_code == 200
            task = response.json()

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
            assert result["pipeline"]["lesion_analysis"] == "success"
            assert result["lesion_analysis"]["enabled"] is True
            assert result["lesion_analysis"]["status"] == "success"
            assert result["lesion_analysis"]["results"][0]["lesion_type"] == "intracranial_hemorrhage"
            assert result["quality_control"]["artifact_reduction"]["model_name"] in {"InDuDoNet", None}
            assert result["quality_control"]["lesion_input_policy"]["used_input"] == "original_ct"
            assert result["quality_control"]["lesion_input_policy"]["corrected_ct_used"] is False
            assert any("InDuDoNet" in warning or "校正" in warning for warning in result["warnings"])
            assert result["report_assist"]["can_enter_report"] is True
            assert "未见明确颅内出血征象" in result["report_assist"]["lesion_text"]
    finally:
        orch.LESION_SERVICE_ENABLED = False


def test_ai_imaging_status_describes_project_ready_chain_without_overclaiming() -> None:
    status = build_ai_imaging_status(
        quality_control={
            "backend": "unet3d",
            "model_name": "metal_unet3d_local",
            "model_version": "local-trained",
            "artifact_reduction": {
                "registered": True,
                "executable": False,
                "model_name": "InDuDoNet",
                "correction_status": "checkpoint_registered_not_executable",
                "use_for_lesion_input": False,
            },
            "lesion_input_policy": {
                "used_input": "original_ct",
                "corrected_ct_used": False,
                "artifact_reduction_status": "checkpoint_registered_not_executable",
            },
        },
        lesion_analysis={
            "status": "success",
            "results": [
                {
                    "lesion_type": "intracranial_hemorrhage",
                    "model_name": "vinbigdata_midl2020_cnn_lstm_ich",
                    "provider": "vinbigdata",
                    "checkpoint_provenance": "mature_public_external_raw",
                    "checkpoint_fallback_used": False,
                    "mask_url": None,
                    "bbox": [],
                    "confidence": 0.71,
                }
            ],
        },
        report_assist={"can_enter_report": True},
    )

    assert status["project_use_status"] == "ready_for_project_demo"
    assert status["workflow_ready"] is True
    assert status["artifact_reduction"]["status"] == "registered_not_executable"
    assert status["lesion_model"]["task_type"] == "classification"
    assert status["lesion_model"]["checkpoint_fallback_used"] is False
    assert status["lesion_model"]["outputs_segmentation"] is False
    assert status["diagnosis_output_policy"]["final_diagnosis_owner"] == "doctor"
    assert "ct_upload_to_report_assist" in status["supported_workflow"]


def test_orchestrator_pipeline_with_model_lesion_detection(tmp_path: Path) -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    checkpoint = tmp_path / "smoke_best.pt"
    create_smoke_checkpoint(checkpoint, base_channels=2, input_shape=(16, 64, 64))
    old_mode = lesion_srv.LESION_MODE
    old_checkpoint = lesion_srv.HEMORRHAGE_CHECKPOINT
    old_device = lesion_srv.HEMORRHAGE_DEVICE
    orch.LESION_SERVICE_ENABLED = True
    orch.LESION_REQUESTED_TYPES = "hemorrhage"
    orch.filter_client = InProcessFilterClient()
    orch.lesion_client = InProcessLesionClient()
    lesion_srv.LESION_MODE = "model"
    lesion_srv.HEMORRHAGE_CHECKPOINT = checkpoint
    lesion_srv.HEMORRHAGE_DEVICE = "cpu"
    try:
        with TestClient(orch.app) as client:
            health_response = client.get("/api/head-ct-ai/health")
            assert health_response.status_code == 200
            health = health_response.json()
            assert health["lesion"]["status"] == "ok"
            assert health["lesion"]["mode"] == "model"
            assert health["lesion"]["models"]["hemorrhage"]["checkpoint_exists"] is True

            with SAMPLE_CT.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-ai/tasks",
                    data={"patient_id": "patient_model_001"},
                    files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
                )
            assert response.status_code == 200
            task = response.json()

            current = task
            for _ in range(60):
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
            assert result["pipeline"]["lesion_analysis"] == "success"
            assert result["lesion_analysis"]["enabled"] is True
            assert result["lesion_analysis"]["status"] == "success"
            lesion_result = result["lesion_analysis"]["results"][0]
            assert lesion_result["lesion_type"] == "intracranial_hemorrhage"
            assert lesion_result["model_name"] == "head_ct_hemorrhage_classifier"
            assert isinstance(lesion_result["confidence"], float)
            assert result["report_assist"]["can_enter_report"] is True
    finally:
        orch.LESION_SERVICE_ENABLED = False
        lesion_srv.LESION_MODE = old_mode
        lesion_srv.HEMORRHAGE_CHECKPOINT = old_checkpoint
        lesion_srv.HEMORRHAGE_DEVICE = old_device


def test_lesion_service_unavailable_marks_task_failed() -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    orch.LESION_SERVICE_ENABLED = True
    orch.filter_client = InProcessFilterClient()
    orch.lesion_client = UnavailableLesionClient()
    try:
        with TestClient(orch.app) as client:
            health_response = client.get("/api/head-ct-ai/health")
            assert health_response.status_code == 200
            health = health_response.json()
            assert health["lesion"]["status"] == "unavailable"

            with SAMPLE_CT.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-ai/tasks",
                    files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
                )
            assert response.status_code == 200
            task = response.json()
            task_response = client.get(task["task_url"])
            assert task_response.status_code == 200
            current = task_response.json()
            assert current["status"] == "failed"
            assert current["error_code"] == "LESION_SERVICE_UNAVAILABLE"
    finally:
        orch.LESION_SERVICE_ENABLED = False


def test_lesion_checkpoint_missing_is_reported(tmp_path: Path) -> None:
    assert SAMPLE_CT.exists(), f"missing smoke sample: {SAMPLE_CT}"
    missing_checkpoint = tmp_path / "missing_best.pt"
    old_mode = lesion_srv.LESION_MODE
    old_checkpoint = lesion_srv.HEMORRHAGE_CHECKPOINT
    old_device = lesion_srv.HEMORRHAGE_DEVICE
    orch.LESION_SERVICE_ENABLED = True
    orch.LESION_REQUESTED_TYPES = "hemorrhage"
    orch.filter_client = InProcessFilterClient()
    orch.lesion_client = InProcessLesionClient()
    lesion_srv.LESION_MODE = "model"
    lesion_srv.HEMORRHAGE_CHECKPOINT = missing_checkpoint
    lesion_srv.HEMORRHAGE_DEVICE = "cpu"
    try:
        with TestClient(orch.app) as client:
            health_response = client.get("/api/head-ct-ai/health")
            assert health_response.status_code == 200
            health = health_response.json()
            assert health["lesion"]["status"] == "degraded"
            assert health["lesion"]["models"]["hemorrhage"]["checkpoint_exists"] is False

            with SAMPLE_CT.open("rb") as file_obj:
                response = client.post(
                    "/api/head-ct-ai/tasks",
                    files={"file": ("sample_ct_positive.nii.gz", file_obj, "application/octet-stream")},
                )
            assert response.status_code == 200
            task = response.json()

            current = task
            for _ in range(30):
                task_response = client.get(task["task_url"])
                assert task_response.status_code == 200
                current = task_response.json()
                if current["status"] in {"success", "failed"}:
                    break
                time.sleep(0.1)

            assert current["status"] == "failed"
            assert current["error_code"] == "LESION_TASK_FAILED"
            assert "MODEL_CHECKPOINT_NOT_FOUND" in current["error_message"]
    finally:
        orch.LESION_SERVICE_ENABLED = False
        lesion_srv.LESION_MODE = old_mode
        lesion_srv.HEMORRHAGE_CHECKPOINT = old_checkpoint
        lesion_srv.HEMORRHAGE_DEVICE = old_device
