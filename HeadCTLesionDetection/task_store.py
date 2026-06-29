"""Local JSON task store for Head CT lesion detection."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException

try:
    from .config import API_PREFIX, MODULE_NAME
except ImportError:  # pragma: no cover - direct script fallback.
    from config import API_PREFIX, MODULE_NAME


TASK_FILE = "task.json"
CASE_CONTEXT_KEYS = ["patient_id", "study_id", "series_id", "report_id", "doctor_id"]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def api_error(status_code: int, error_code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"status": "failed", "error_code": error_code, "message": message})


def normalize_case_context(case_context: Optional[dict[str, Any]]) -> dict[str, Any]:
    payload = {key: None for key in CASE_CONTEXT_KEYS}
    if case_context:
        payload.update({key: case_context.get(key) for key in CASE_CONTEXT_KEYS})
    return payload


def validate_task_id(task_id: str) -> str:
    allowed = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ._-")
    if not task_id or any(char not in allowed for char in task_id):
        raise api_error(400, "INVALID_TASK_ID", "非法 task_id")
    return task_id


def task_dir(output_root: Path, task_id: str) -> Path:
    validate_task_id(task_id)
    path = (output_root / task_id).resolve()
    root = output_root.resolve()
    if root not in path.parents:
        raise api_error(400, "INVALID_TASK_PATH", "非法任务路径")
    return path


def task_file(output_root: Path, task_id: str) -> Path:
    return task_dir(output_root, task_id) / TASK_FILE


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def create_task_record(
    *,
    output_root: Path,
    task_id: str,
    original_file: str,
    input_file: str,
    case_context: Optional[dict[str, Any]],
    requested_lesions: list[str],
) -> dict[str, Any]:
    output_dir = task_dir(output_root, task_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "task_id": task_id,
        "status": "queued",
        "module": MODULE_NAME,
        "case_context": normalize_case_context(case_context),
        "requested_lesions": requested_lesions,
        "created_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "elapsed_ms": None,
        "original_file": original_file,
        "input_file": input_file,
        "result_file": "lesion_result.json",
        "error_code": None,
        "error_message": None,
        "task_url": f"{API_PREFIX}/tasks/{task_id}",
        "result_url": f"{API_PREFIX}/results/{task_id}",
    }
    write_json(output_dir / TASK_FILE, payload)
    return payload


def read_task_record(output_root: Path, task_id: str) -> dict[str, Any]:
    path = task_file(output_root, task_id)
    if not path.exists():
        raise api_error(404, "TASK_NOT_FOUND", "任务不存在")
    return read_json(path)


def update_task_record(output_root: Path, task_id: str, **changes: Any) -> dict[str, Any]:
    payload = read_task_record(output_root, task_id)
    payload.update(changes)
    write_json(task_file(output_root, task_id), payload)
    return payload


def mark_running(output_root: Path, task_id: str) -> dict[str, Any]:
    return update_task_record(output_root, task_id, status="running", started_at=now_iso(), error_code=None, error_message=None)


def mark_success(output_root: Path, task_id: str, elapsed_ms: int) -> dict[str, Any]:
    return update_task_record(
        output_root,
        task_id,
        status="success",
        finished_at=now_iso(),
        elapsed_ms=elapsed_ms,
        result_url=f"{API_PREFIX}/results/{task_id}",
        error_code=None,
        error_message=None,
    )


def mark_failed(output_root: Path, task_id: str, error_code: str, error_message: str, elapsed_ms: Optional[int] = None) -> dict[str, Any]:
    return update_task_record(
        output_root,
        task_id,
        status="failed",
        finished_at=now_iso(),
        elapsed_ms=elapsed_ms,
        error_code=error_code,
        error_message=error_message,
    )
