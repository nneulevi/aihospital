"""Local JSON review store for doctor review workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .config import API_PREFIX
    from .task_store import api_error, now_iso, read_task_record, task_dir, write_json
except ImportError:  # pragma: no cover - direct script fallback.
    from config import API_PREFIX
    from task_store import api_error, now_iso, read_task_record, task_dir, write_json


REVIEW_FILE = "review.json"
REVIEW_EVENTS_FILE = "review_events.jsonl"
REVIEW_STATUSES = {"pending", "confirmed", "modified", "rejected", "needs_follow_up"}
SUBMITTABLE_REVIEW_STATUSES = REVIEW_STATUSES - {"pending"}


def review_file(output_root: Path, task_id: str) -> Path:
    return task_dir(output_root, task_id) / REVIEW_FILE


def review_events_file(output_root: Path, task_id: str) -> Path:
    return task_dir(output_root, task_id) / REVIEW_EVENTS_FILE


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def append_review_event(output_root: Path, task_id: str, event: dict[str, Any]) -> None:
    path = review_events_file(output_root, task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(event, ensure_ascii=False) + "\n")


def pending_review(task_record: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task_record.get("task_id"))
    return {
        "task_id": task_id,
        "review_status": "pending",
        "doctor_id": None,
        "reviewed_at": None,
        "doctor_comment": None,
        "artifact_review": {},
        "lesion_review": {},
        "report_review": {},
        "safety": {},
        "source_result_url": task_record.get("result_url") or f"{API_PREFIX}/results/{task_id}",
        "created_at": None,
        "updated_at": None,
    }


def read_review(output_root: Path, task_id: str) -> dict[str, Any]:
    task_record = read_task_record(output_root, task_id)
    path = review_file(output_root, task_id)
    if not path.exists():
        return pending_review(task_record)
    return read_json(path)


def validate_review_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise api_error(400, "INVALID_REVIEW_PAYLOAD", "审核请求体必须是 JSON 对象")
    status = payload.get("review_status")
    if status not in SUBMITTABLE_REVIEW_STATUSES:
        allowed = ", ".join(sorted(SUBMITTABLE_REVIEW_STATUSES))
        raise api_error(400, "INVALID_REVIEW_STATUS", f"review_status 必须是: {allowed}")
    doctor_id = payload.get("doctor_id")
    if doctor_id is not None and not isinstance(doctor_id, str):
        raise api_error(400, "INVALID_REVIEW_PAYLOAD", "doctor_id 必须是字符串")
    for field in ["artifact_review", "lesion_review", "report_review", "safety"]:
        if field in payload and payload[field] is not None and not isinstance(payload[field], dict):
            raise api_error(400, "INVALID_REVIEW_PAYLOAD", f"{field} 必须是 JSON 对象")


def create_or_update_review(output_root: Path, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    task_record = read_task_record(output_root, task_id)
    if task_record.get("status") != "success":
        raise api_error(409, "TASK_NOT_SUCCESS", "只允许对已成功完成的任务提交医生审核")
    validate_review_payload(payload)

    existing_path = review_file(output_root, task_id)
    existing = read_json(existing_path) if existing_path.exists() else {}
    created_at = existing.get("created_at") or now_iso()
    updated_at = now_iso()
    review = {
        "task_id": task_id,
        "review_status": payload["review_status"],
        "doctor_id": payload.get("doctor_id"),
        "reviewed_at": payload.get("reviewed_at") or updated_at,
        "doctor_comment": payload.get("doctor_comment"),
        "artifact_review": payload.get("artifact_review") or {},
        "lesion_review": payload.get("lesion_review") or {},
        "report_review": payload.get("report_review") or {},
        "safety": payload.get("safety") or {},
        "source_result_url": task_record.get("result_url") or f"{API_PREFIX}/results/{task_id}",
        "created_at": created_at,
        "updated_at": updated_at,
    }
    write_json(existing_path, review)
    append_review_event(
        output_root,
        task_id,
        {
            "event": "review_updated",
            "task_id": task_id,
            "review_status": review["review_status"],
            "doctor_id": review["doctor_id"],
            "created_at": updated_at,
        },
    )
    return review
