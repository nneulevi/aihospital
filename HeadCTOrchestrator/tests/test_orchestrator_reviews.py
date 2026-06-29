from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from HeadCTOrchestrator import OrchestratorServer as orch


def _make_task(tmp_path: Path, task_id: str = "review_task_001", *, status: str = "success") -> dict[str, Any]:
    old_root = orch.OUTPUT_ROOT
    orch.OUTPUT_ROOT = tmp_path
    task = orch.create_task_record(
        output_root=tmp_path,
        task_id=task_id,
        original_file="input.nii.gz",
        input_file="input.nii.gz",
        case_context={"patient_id": "patient_001", "doctor_id": "doctor_001"},
    )
    result = {
        "task_id": task_id,
        "status": "success",
        "quality_control": {"severity": "mild"},
        "lesion_analysis": {"status": "success", "results": []},
        "report_assist": {
            "summary": "AI 结果仅供辅助参考，最终结论需医生审核。",
            "requires_doctor_review": True,
        },
    }
    orch.write_json(tmp_path / task_id / "orchestrator_result.json", result)
    if status == "success":
        task = orch.mark_success(tmp_path, task_id, 100)
    else:
        task = orch.mark_failed(tmp_path, task_id, "FILTER_UNAVAILABLE", "Filter unavailable", 100)
    orch.OUTPUT_ROOT = old_root
    return task


def _review_payload(status: str = "confirmed") -> dict[str, Any]:
    return {
        "review_status": status,
        "doctor_id": "doctor_001",
        "doctor_comment": "已结合原始影像复核。",
        "artifact_review": {
            "accepted": True,
            "severity_override": None,
            "comment": "质控结果符合阅片感受。",
        },
        "lesion_review": {
            "accepted": True,
            "lesion_overrides": [],
            "comment": "病灶识别结果仅作参考。",
        },
        "report_review": {
            "ai_summary_used": True,
            "final_report_text": "医生最终报告文本。",
            "final_report_used": True,
        },
        "safety": {
            "doctor_confirmed_ai_is_reference_only": True,
            "requires_follow_up": False,
        },
    }


def test_get_review_pending_for_existing_task(tmp_path: Path) -> None:
    old_root = orch.OUTPUT_ROOT
    orch.OUTPUT_ROOT = tmp_path
    try:
        _make_task(tmp_path, "pending_task")
        with TestClient(orch.app) as client:
            response = client.get("/api/head-ct-ai/reviews/pending_task")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["review"]["task_id"] == "pending_task"
        assert payload["review"]["review_status"] == "pending"
    finally:
        orch.OUTPUT_ROOT = old_root


def test_create_review_for_success_task(tmp_path: Path) -> None:
    old_root = orch.OUTPUT_ROOT
    orch.OUTPUT_ROOT = tmp_path
    try:
        _make_task(tmp_path, "success_task")
        with TestClient(orch.app) as client:
            response = client.post("/api/head-ct-ai/reviews/success_task", json=_review_payload("modified"))
        assert response.status_code == 200
        payload = response.json()
        review = payload["review"]
        assert payload["status"] == "success"
        assert review["task_id"] == "success_task"
        assert review["review_status"] == "modified"
        assert review["doctor_id"] == "doctor_001"
        assert review["source_result_url"] == "/api/head-ct-ai/results/success_task"
        assert (tmp_path / "success_task" / "review.json").exists()
    finally:
        orch.OUTPUT_ROOT = old_root


def test_create_review_requires_existing_task(tmp_path: Path) -> None:
    old_root = orch.OUTPUT_ROOT
    orch.OUTPUT_ROOT = tmp_path
    try:
        with TestClient(orch.app) as client:
            response = client.post("/api/head-ct-ai/reviews/missing_task", json=_review_payload())
        assert response.status_code == 404
        assert response.json()["error_code"] == "TASK_NOT_FOUND"
    finally:
        orch.OUTPUT_ROOT = old_root


def test_create_review_requires_success_task(tmp_path: Path) -> None:
    old_root = orch.OUTPUT_ROOT
    orch.OUTPUT_ROOT = tmp_path
    try:
        _make_task(tmp_path, "failed_task", status="failed")
        with TestClient(orch.app) as client:
            response = client.post("/api/head-ct-ai/reviews/failed_task", json=_review_payload())
        assert response.status_code == 409
        assert response.json()["error_code"] == "TASK_NOT_SUCCESS"
    finally:
        orch.OUTPUT_ROOT = old_root


def test_review_status_validation(tmp_path: Path) -> None:
    old_root = orch.OUTPUT_ROOT
    orch.OUTPUT_ROOT = tmp_path
    try:
        _make_task(tmp_path, "invalid_status_task")
        payload = _review_payload("bad_status")
        with TestClient(orch.app) as client:
            response = client.post("/api/head-ct-ai/reviews/invalid_status_task", json=payload)
        assert response.status_code == 400
        assert response.json()["error_code"] == "INVALID_REVIEW_STATUS"
    finally:
        orch.OUTPUT_ROOT = old_root


def test_review_event_log_appended(tmp_path: Path) -> None:
    old_root = orch.OUTPUT_ROOT
    orch.OUTPUT_ROOT = tmp_path
    try:
        _make_task(tmp_path, "event_task")
        with TestClient(orch.app) as client:
            first = client.post("/api/head-ct-ai/reviews/event_task", json=_review_payload("confirmed"))
            second = client.post("/api/head-ct-ai/reviews/event_task", json=_review_payload("modified"))
        assert first.status_code == 200
        assert second.status_code == 200
        event_path = tmp_path / "event_task" / "review_events.jsonl"
        events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
        assert len(events) == 2
        assert events[0]["review_status"] == "confirmed"
        assert events[1]["review_status"] == "modified"
    finally:
        orch.OUTPUT_ROOT = old_root


def test_review_does_not_modify_original_orchestrator_result(tmp_path: Path) -> None:
    old_root = orch.OUTPUT_ROOT
    orch.OUTPUT_ROOT = tmp_path
    try:
        _make_task(tmp_path, "immutable_result_task")
        result_path = tmp_path / "immutable_result_task" / "orchestrator_result.json"
        before = result_path.read_bytes()
        with TestClient(orch.app) as client:
            response = client.post("/api/head-ct-ai/reviews/immutable_result_task", json=_review_payload())
        assert response.status_code == 200
        after = result_path.read_bytes()
        assert before == after
    finally:
        orch.OUTPUT_ROOT = old_root
