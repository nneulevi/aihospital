"""Local JSON task store for CT artifact background inference."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ct_artifact_contract import API_PREFIX, ApiErrorCode, api_error, validate_request_id


TASK_FILE = "task.json"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def task_dir(output_root: Path, task_id: str) -> Path:
    validate_request_id(task_id)
    path = (output_root / task_id).resolve()
    root = output_root.resolve()
    if root not in path.parents:
        raise api_error(400, ApiErrorCode.INVALID_RESULT_FILE, "非法任务路径")
    return path


def task_file(output_root: Path, task_id: str) -> Path:
    return task_dir(output_root, task_id) / TASK_FILE


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def create_task_record(
    *,
    output_root: Path,
    task_id: str,
    backend: str,
    model_name: str,
    model_version: str,
    original_file: str,
    input_file: str,
) -> dict[str, Any]:
    output_dir = task_dir(output_root, task_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "task_id": task_id,
        "request_id": task_id,
        "status": "queued",
        "module": "ct_artifact_filter",
        "backend": backend,
        "model_name": model_name,
        "model_version": model_version,
        "created_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "elapsed_ms": None,
        "original_file": original_file,
        "input_file": input_file,
        "result_file": "result.json",
        "error_code": None,
        "error_message": None,
        "task_url": f"{API_PREFIX}/tasks/{task_id}",
        "result_url": f"{API_PREFIX}/results/{task_id}",
        "mask_url": f"{API_PREFIX}/files/{task_id}/mask.nii.gz",
    }
    write_json_atomic(output_dir / TASK_FILE, payload)
    return payload


def read_task_record(output_root: Path, task_id: str) -> dict[str, Any]:
    path = task_file(output_root, task_id)
    if not path.exists():
        raise api_error(404, ApiErrorCode.TASK_NOT_FOUND, "任务不存在")
    return json.loads(path.read_text(encoding="utf-8"))


def update_task_record(output_root: Path, task_id: str, **changes: Any) -> dict[str, Any]:
    payload = read_task_record(output_root, task_id)
    payload.update(changes)
    write_json_atomic(task_file(output_root, task_id), payload)
    return payload


def mark_task_running(output_root: Path, task_id: str) -> dict[str, Any]:
    return update_task_record(
        output_root,
        task_id,
        status="running",
        started_at=now_iso(),
        error_code=None,
        error_message=None,
    )


def mark_task_success(
    *,
    output_root: Path,
    task_id: str,
    elapsed_ms: int,
    preview_urls: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    return update_task_record(
        output_root,
        task_id,
        status="success",
        finished_at=now_iso(),
        elapsed_ms=elapsed_ms,
        result_url=f"{API_PREFIX}/results/{task_id}",
        mask_url=f"{API_PREFIX}/files/{task_id}/mask.nii.gz",
        preview_urls=preview_urls or {},
        error_code=None,
        error_message=None,
    )


def mark_task_failed(
    *,
    output_root: Path,
    task_id: str,
    error_code: str,
    error_message: str,
    elapsed_ms: Optional[int] = None,
) -> dict[str, Any]:
    return update_task_record(
        output_root,
        task_id,
        status="failed",
        finished_at=now_iso(),
        elapsed_ms=elapsed_ms,
        error_code=error_code,
        error_message=error_message,
    )
