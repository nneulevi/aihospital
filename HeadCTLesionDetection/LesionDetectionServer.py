"""FastAPI service for Head CT lesion detection."""

from __future__ import annotations

import json
import shutil
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

try:
    from .config import (
        API_PREFIX,
        DEFAULT_REQUESTED_LESIONS,
        HEMORRHAGE_CHECKPOINT,
        HEMORRHAGE_ALLOW_INFERENCE_FALLBACK,
        HEMORRHAGE_CHECKPOINT_FALLBACK_USED,
        HEMORRHAGE_CHECKPOINT_PROVENANCE,
        HEMORRHAGE_DEVICE,
        HEMORRHAGE_FALLBACK_CHECKPOINT,
        HEMORRHAGE_MATURE_CANDIDATE_PATHS,
        HEMORRHAGE_MODEL_PROVIDER,
        HOST,
        LESION_MODE,
        MODEL_SUPPORTED_LESIONS,
        MODULE_NAME,
        MODULE_VERSION,
        OUTPUT_ROOT,
        PORT,
        VINBIGDATA_CHECKPOINT,
        VINBIGDATA_IMAGE_SIZE,
        VINBIGDATA_MAX_SLICES,
        VINBIGDATA_THRESHOLD,
        SUPPORTED_LESIONS,
    )
    from .task_store import api_error, create_task_record, mark_failed, mark_running, mark_success, read_task_record, task_dir, write_json
    from .models.hemorrhage.infer import predict_hemorrhage, predict_vinbigdata_hemorrhage
except ImportError:  # pragma: no cover - direct script fallback.
    from config import (
        API_PREFIX,
        DEFAULT_REQUESTED_LESIONS,
        HEMORRHAGE_CHECKPOINT,
        HEMORRHAGE_ALLOW_INFERENCE_FALLBACK,
        HEMORRHAGE_CHECKPOINT_FALLBACK_USED,
        HEMORRHAGE_CHECKPOINT_PROVENANCE,
        HEMORRHAGE_DEVICE,
        HEMORRHAGE_FALLBACK_CHECKPOINT,
        HEMORRHAGE_MATURE_CANDIDATE_PATHS,
        HEMORRHAGE_MODEL_PROVIDER,
        HOST,
        LESION_MODE,
        MODEL_SUPPORTED_LESIONS,
        MODULE_NAME,
        MODULE_VERSION,
        OUTPUT_ROOT,
        PORT,
        VINBIGDATA_CHECKPOINT,
        VINBIGDATA_IMAGE_SIZE,
        VINBIGDATA_MAX_SLICES,
        VINBIGDATA_THRESHOLD,
        SUPPORTED_LESIONS,
    )
    from task_store import api_error, create_task_record, mark_failed, mark_running, mark_success, read_task_record, task_dir, write_json
    from models.hemorrhage.infer import predict_hemorrhage, predict_vinbigdata_hemorrhage


class LesionErrorCode:
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    INVALID_LESION_MODE = "INVALID_LESION_MODE"
    UNSUPPORTED_LESION_TYPE = "UNSUPPORTED_LESION_TYPE"
    QUALITY_CONTEXT_INVALID = "QUALITY_CONTEXT_INVALID"
    MODEL_CHECKPOINT_NOT_FOUND = "MODEL_CHECKPOINT_NOT_FOUND"
    INFERENCE_FAILED = "INFERENCE_FAILED"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    RESULT_NOT_FOUND = "RESULT_NOT_FOUND"


def ensure_dirs() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def is_nifti_file(filename: str) -> bool:
    return filename.lower().endswith((".nii", ".nii.gz"))


def strip_nifti_suffix(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".nii.gz"):
        return filename[:-7]
    if lower.endswith(".nii"):
        return filename[:-4]
    return Path(filename).stem


def safe_original_name(filename: Optional[str]) -> str:
    name = Path(filename or "ct.nii.gz").name
    suffix = ".nii.gz" if name.lower().endswith(".nii.gz") else Path(name).suffix
    stem = strip_nifti_suffix(name)
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in stem).strip("._-") or "ct"
    return f"{safe}{suffix}"


def task_input_name(filename: str) -> str:
    return "input.nii.gz" if filename.lower().endswith(".nii.gz") else "input.nii"


def parse_json_field(text: Optional[str], field_name: str) -> dict[str, Any]:
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise api_error(400, f"{field_name.upper()}_INVALID", f"{field_name} 不是合法 JSON") from exc
    if not isinstance(payload, dict):
        raise api_error(400, f"{field_name.upper()}_INVALID", f"{field_name} 必须是 JSON 对象")
    return payload


def parse_requested_lesions(text: Optional[str]) -> list[str]:
    raw = text or DEFAULT_REQUESTED_LESIONS
    lesions = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not lesions:
        lesions = ["hemorrhage"]
    unsupported = [item for item in lesions if item not in SUPPORTED_LESIONS]
    if unsupported:
        raise api_error(400, LesionErrorCode.UNSUPPORTED_LESION_TYPE, f"不支持的病灶类型: {', '.join(unsupported)}")
    return lesions


def current_mode() -> str:
    mode = LESION_MODE.strip().lower()
    if mode not in {"mock", "model"}:
        raise api_error(500, LesionErrorCode.INVALID_LESION_MODE, f"Unsupported LESION_MODE: {LESION_MODE}")
    return mode


def current_model_provider() -> str:
    provider = HEMORRHAGE_MODEL_PROVIDER.strip().lower()
    if provider not in {"local", "vinbigdata"}:
        raise api_error(500, LesionErrorCode.INVALID_LESION_MODE, f"Unsupported HEMORRHAGE_MODEL_PROVIDER: {HEMORRHAGE_MODEL_PROVIDER}")
    return provider


def validate_requested_lesions_for_mode(requested_lesions: list[str], mode: str) -> None:
    if mode != "model":
        return
    unsupported = [item for item in requested_lesions if item not in MODEL_SUPPORTED_LESIONS]
    if unsupported:
        raise api_error(
            400,
            LesionErrorCode.UNSUPPORTED_LESION_TYPE,
            f"Model mode currently supports only: {', '.join(sorted(MODEL_SUPPORTED_LESIONS))}; unsupported: {', '.join(unsupported)}",
        )


def checkpoint_status() -> dict[str, Any]:
    provider = current_model_provider()
    checkpoint = Path(VINBIGDATA_CHECKPOINT if provider == "vinbigdata" else HEMORRHAGE_CHECKPOINT)
    candidate_paths = [Path(item) for item in HEMORRHAGE_MATURE_CANDIDATE_PATHS]
    return {
        "hemorrhage": {
            "configured": bool(str(checkpoint)),
            "provider": provider,
            "checkpoint": str(checkpoint),
            "checkpoint_exists": checkpoint.exists(),
            "checkpoint_provenance": HEMORRHAGE_CHECKPOINT_PROVENANCE,
            "checkpoint_fallback_used": HEMORRHAGE_CHECKPOINT_FALLBACK_USED,
            "fallback_checkpoint": str(HEMORRHAGE_FALLBACK_CHECKPOINT),
            "fallback_checkpoint_exists": Path(HEMORRHAGE_FALLBACK_CHECKPOINT).exists(),
            "mature_candidate_paths": [str(path) for path in candidate_paths],
            "mature_candidate_exists": any(path.exists() for path in candidate_paths),
            "allow_inference_fallback": HEMORRHAGE_ALLOW_INFERENCE_FALLBACK,
            "device": HEMORRHAGE_DEVICE,
            "vinbigdata": {
                "checkpoint": str(VINBIGDATA_CHECKPOINT),
                "checkpoint_exists": Path(VINBIGDATA_CHECKPOINT).exists(),
                "image_size": VINBIGDATA_IMAGE_SIZE,
                "max_slices": VINBIGDATA_MAX_SLICES,
                "threshold": VINBIGDATA_THRESHOLD,
            },
        }
    }


def reliability_from_quality(quality_context: dict[str, Any]) -> str:
    severity = str(quality_context.get("severity") or "none")
    if severity == "none":
        return "normal"
    if severity == "mild":
        return "slightly_limited_by_artifact"
    if severity == "moderate":
        return "limited_by_artifact"
    return "strongly_limited_by_artifact"


def warnings_from_quality(quality_context: dict[str, Any]) -> list[str]:
    severity = str(quality_context.get("severity") or "none")
    artifact_reduction = quality_context.get("artifact_reduction") or {}
    warnings: list[str] = []
    if severity == "none":
        warnings = []
    elif severity == "mild":
        warnings = ["存在轻度金属伪影，建议结合原始影像复核。"]
    elif severity == "moderate":
        warnings = ["存在中度金属伪影，受影响层面附近结果需谨慎解释。"]
    else:
        warnings = ["存在重度金属伪影，病灶识别结果可信度可能明显受限。"]
    reduction_warning = artifact_reduction.get("warning")
    if reduction_warning and not artifact_reduction.get("use_for_lesion_input"):
        warnings.append(str(reduction_warning))
    return list(dict.fromkeys(warnings))


def build_input_policy(quality_context: dict[str, Any]) -> dict[str, Any]:
    artifact_reduction = quality_context.get("artifact_reduction") or {}
    corrected_ct_url = artifact_reduction.get("corrected_ct_url")
    use_corrected = bool(artifact_reduction.get("use_for_lesion_input") and corrected_ct_url)
    return {
        "used_input": "corrected_ct" if use_corrected else "original_ct",
        "corrected_ct_used": use_corrected,
        "corrected_ct_url": corrected_ct_url if use_corrected else None,
        "artifact_reduction_status": artifact_reduction.get("correction_status", "not_configured"),
        "artifact_reduction_model": artifact_reduction.get("model_name"),
        "reason": (
            "使用金属伪影校正 CT 进行病灶识别。"
            if use_corrected
            else "未获得可执行的金属伪影校正 CT，病灶识别使用原始 CT。"
        ),
    }


def mock_lesion_result(lesion_key: str, quality_context: dict[str, Any]) -> dict[str, Any]:
    spec = SUPPORTED_LESIONS[lesion_key]
    warnings = warnings_from_quality(quality_context)
    confidence = 0.05 if lesion_key == "hemorrhage" else 0.04
    return {
        "lesion_type": spec["lesion_type"],
        "display_name": spec["display_name"],
        "detected": False,
        "confidence": confidence,
        "severity": "none",
        "affected_slices": [],
        "locations": [],
        "bbox": [],
        "mask_url": None,
        "preview_urls": {},
        "model_name": spec["model_name"],
        "model_version": spec["model_version"],
        "reliability": reliability_from_quality(quality_context),
        "warnings": warnings,
        "report_suggestion": spec["negative_suggestion"],
    }


def build_lesion_result(
    *,
    task_id: str,
    task_record: dict[str, Any],
    quality_context: dict[str, Any],
    requested_lesions: list[str],
    elapsed_ms: int,
    inference_mode: str,
    results: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    if results is None:
        results = [mock_lesion_result(lesion, quality_context) for lesion in requested_lesions]
    positive = [item["lesion_type"] for item in results if item["detected"]]
    highest_confidence = max((float(item["confidence"]) for item in results), default=0.0)
    warnings = list(dict.fromkeys(warning for item in results for warning in (item.get("warnings") or [])))
    return {
        "task_id": task_id,
        "status": "success",
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "inference_mode": inference_mode,
        "case_context": task_record.get("case_context"),
        "quality_context": quality_context,
        "input_policy": build_input_policy(quality_context),
        "requested_lesions": requested_lesions,
        "results": results,
        "warnings": warnings,
        "summary": {
            "detected_lesion_count": len(positive),
            "positive_lesion_types": positive,
            "highest_confidence": highest_confidence,
        },
        "elapsed_ms": elapsed_ms,
        "error_code": None,
        "error_message": None,
    }


def build_model_results(input_path: Path, quality_context: dict[str, Any], requested_lesions: list[str]) -> list[dict[str, Any]]:
    provider = current_model_provider()
    checkpoint = Path(VINBIGDATA_CHECKPOINT if provider == "vinbigdata" else HEMORRHAGE_CHECKPOINT)
    fallback_checkpoint = Path(HEMORRHAGE_FALLBACK_CHECKPOINT)
    if not checkpoint.exists():
        if not HEMORRHAGE_ALLOW_INFERENCE_FALLBACK or not fallback_checkpoint.exists() or fallback_checkpoint == checkpoint:
            raise FileNotFoundError(f"Hemorrhage checkpoint not found: {checkpoint}")
        provider = "local_fallback"
        checkpoint = fallback_checkpoint
    results: list[dict[str, Any]] = []
    for lesion in requested_lesions:
        if lesion == "hemorrhage":
            if provider == "vinbigdata":
                try:
                    result = predict_vinbigdata_hemorrhage(
                        nifti_path=input_path,
                        checkpoint_path=checkpoint,
                        device=HEMORRHAGE_DEVICE,
                        quality_context=quality_context,
                        threshold=VINBIGDATA_THRESHOLD,
                        image_size=VINBIGDATA_IMAGE_SIZE,
                        max_slices=VINBIGDATA_MAX_SLICES,
                    )
                    result.update(
                        {
                            "checkpoint_path": str(checkpoint),
                            "checkpoint_provenance": HEMORRHAGE_CHECKPOINT_PROVENANCE,
                            "checkpoint_fallback_used": False,
                        }
                    )
                except Exception as exc:
                    if not HEMORRHAGE_ALLOW_INFERENCE_FALLBACK or not fallback_checkpoint.exists():
                        raise
                    result = predict_hemorrhage(
                        input_path,
                        fallback_checkpoint,
                        device=HEMORRHAGE_DEVICE,
                        quality_context=quality_context,
                    )
                    result.update(
                        {
                            "provider": "local_fallback",
                            "checkpoint_path": str(fallback_checkpoint),
                            "checkpoint_provenance": "fallback_after_mature_inference_error",
                            "checkpoint_fallback_used": True,
                            "checkpoint_fallback_reason": str(exc),
                            "preferred_checkpoint_path": str(checkpoint),
                        }
                    )
                results.append(result)
            else:
                result = predict_hemorrhage(
                    input_path,
                    checkpoint,
                    device=HEMORRHAGE_DEVICE,
                    quality_context=quality_context,
                )
                result.update(
                    {
                        "checkpoint_path": str(checkpoint),
                        "checkpoint_provenance": HEMORRHAGE_CHECKPOINT_PROVENANCE,
                        "checkpoint_fallback_used": HEMORRHAGE_CHECKPOINT_FALLBACK_USED,
                    }
                )
                results.append(result)
    return results


def run_mock_inference(task_id: str, quality_context: dict[str, Any], requested_lesions: list[str]) -> None:
    started = time.perf_counter()
    try:
        mark_running(OUTPUT_ROOT, task_id)
        task_record = read_task_record(OUTPUT_ROOT, task_id)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        result = build_lesion_result(
            task_id=task_id,
            task_record=task_record,
            quality_context=quality_context,
            requested_lesions=requested_lesions,
            elapsed_ms=elapsed_ms,
            inference_mode="mock",
        )
        write_json(task_dir(OUTPUT_ROOT, task_id) / "lesion_result.json", result)
        mark_success(OUTPUT_ROOT, task_id, elapsed_ms)
    except Exception as exc:
        mark_failed(OUTPUT_ROOT, task_id, LesionErrorCode.INFERENCE_FAILED, str(exc), int((time.perf_counter() - started) * 1000))


def run_model_inference(task_id: str, quality_context: dict[str, Any], requested_lesions: list[str]) -> None:
    started = time.perf_counter()
    try:
        mark_running(OUTPUT_ROOT, task_id)
        task_record = read_task_record(OUTPUT_ROOT, task_id)
        input_path = task_dir(OUTPUT_ROOT, task_id) / str(task_record["input_file"])
        model_results = build_model_results(input_path, quality_context, requested_lesions)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        result = build_lesion_result(
            task_id=task_id,
            task_record=task_record,
            quality_context=quality_context,
            requested_lesions=requested_lesions,
            elapsed_ms=elapsed_ms,
            inference_mode="model",
            results=model_results,
        )
        write_json(task_dir(OUTPUT_ROOT, task_id) / "lesion_result.json", result)
        mark_success(OUTPUT_ROOT, task_id, elapsed_ms)
    except FileNotFoundError as exc:
        mark_failed(
            OUTPUT_ROOT,
            task_id,
            LesionErrorCode.MODEL_CHECKPOINT_NOT_FOUND,
            str(exc),
            int((time.perf_counter() - started) * 1000),
        )
    except Exception as exc:
        mark_failed(OUTPUT_ROOT, task_id, LesionErrorCode.INFERENCE_FAILED, str(exc), int((time.perf_counter() - started) * 1000))


def run_inference_task(task_id: str, mode: str, quality_context: dict[str, Any], requested_lesions: list[str]) -> None:
    if mode == "model":
        run_model_inference(task_id, quality_context, requested_lesions)
    else:
        run_mock_inference(task_id, quality_context, requested_lesions)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_dirs()
    yield


async def http_exception_handler(_: Any, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"status": "failed", "error_code": f"HTTP_{exc.status_code}", "message": str(exc.detail)})


app = FastAPI(title="头部 CT 病灶识别服务", version=MODULE_VERSION, lifespan=lifespan)
app.add_exception_handler(HTTPException, http_exception_handler)


@app.get("/")
async def root():
    return {"status": "ok", "module": MODULE_NAME, "health": f"{API_PREFIX}/health", "tasks": f"{API_PREFIX}/tasks"}


@app.get(f"{API_PREFIX}/health")
async def health():
    mode = current_mode()
    model_status = checkpoint_status()
    checkpoint_exists = bool(model_status["hemorrhage"]["checkpoint_exists"])
    return {
        "status": "ok" if mode == "mock" or checkpoint_exists else "degraded",
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "mode": mode,
        "model_provider": current_model_provider(),
        "supported_lesions": list(SUPPORTED_LESIONS.keys()),
        "model_supported_lesions": sorted(MODEL_SUPPORTED_LESIONS),
        "models": model_status,
        "storage": {"outputs": str(OUTPUT_ROOT.resolve()), "outputs_exists": OUTPUT_ROOT.exists()},
    }


@app.post(f"{API_PREFIX}/tasks")
async def create_lesion_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    case_context: Optional[str] = Form(None),
    quality_context: Optional[str] = Form(None),
    requested_lesions: Optional[str] = Form(None),
):
    if not is_nifti_file(file.filename or ""):
        raise api_error(400, LesionErrorCode.INVALID_FILE_TYPE, "只支持 .nii 或 .nii.gz 格式的 CT 文件")
    ensure_dirs()
    case_payload = parse_json_field(case_context, "case_context")
    quality_payload = parse_json_field(quality_context, "quality_context")
    mode = current_mode()
    lesion_keys = parse_requested_lesions(requested_lesions)
    validate_requested_lesions_for_mode(lesion_keys, mode)
    task_id = uuid.uuid4().hex
    original_filename = safe_original_name(file.filename)
    output_dir = task_dir(OUTPUT_ROOT, task_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = output_dir / task_input_name(original_filename)
    try:
        with input_path.open("wb") as dst:
            shutil.copyfileobj(file.file, dst)
        task = create_task_record(
            output_root=OUTPUT_ROOT,
            task_id=task_id,
            original_file=original_filename,
            input_file=input_path.name,
            case_context=case_payload,
            requested_lesions=lesion_keys,
        )
        write_json(output_dir / "quality_context.json", quality_payload)
        background_tasks.add_task(run_inference_task, task_id, mode, quality_payload, lesion_keys)
        return task
    finally:
        try:
            await file.close()
        except Exception:
            pass


@app.get(f"{API_PREFIX}/tasks/{{task_id}}")
async def get_lesion_task(task_id: str):
    return read_task_record(OUTPUT_ROOT, task_id)


@app.get(f"{API_PREFIX}/results/{{task_id}}")
async def get_lesion_result(task_id: str):
    path = task_dir(OUTPUT_ROOT, task_id) / "lesion_result.json"
    if not path.exists():
        raise api_error(404, LesionErrorCode.RESULT_NOT_FOUND, "病灶识别结果不存在")
    return FileResponse(path, media_type="application/json", filename=path.name)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("LesionDetectionServer:app", host=HOST, port=PORT, reload=False)
