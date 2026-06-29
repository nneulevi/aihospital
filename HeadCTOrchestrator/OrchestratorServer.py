"""FastAPI service that orchestrates Head CT AI analysis modules."""

from __future__ import annotations

import sys
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
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
        FILTER_BASE_URL,
        FILTER_POLL_INTERVAL_SECONDS,
        FILTER_POLL_MAX_ATTEMPTS,
        FILTER_TIMEOUT_SECONDS,
        LESION_BASE_URL,
        LESION_POLL_INTERVAL_SECONDS,
        LESION_POLL_MAX_ATTEMPTS,
        LESION_REQUESTED_TYPES,
        LESION_SKIP_ON_SEVERE_ARTIFACT,
        HOST,
        LESION_SERVICE_ENABLED,
        LESION_TIMEOUT_SECONDS,
        MODULE_NAME,
        MODULE_VERSION,
        OUTPUT_ROOT,
        PORT,
        RAG_ENABLED,
    )
    from .rag.db import health as rag_db_health
    from .rag.llm_provider import LlmProviderError
    from .rag.report_enhancer import ReportEnhancementError, enhance_report_assist
    from .rag.retriever import RagRetrievalError
    from .rag.clinical_assist import (
        ClinicalAssistError,
        generate_consultation_assist,
        generate_diagnosis_assist,
    )
    from .ai_imaging_readiness import build_ai_imaging_status
    from .dicom_ingest import (
        DicomIngestError,
        is_supported_ct_upload,
        normalize_saved_upload,
        safe_original_name,
        save_upload_stream,
    )
    from .service_clients.filter_client import FilterClient, HttpFilterClient
    from .service_clients.lesion_client import HttpLesionClient, LesionClient
    from .review_store import create_or_update_review, read_review
    from .task_store import (
        api_error,
        create_task_record,
        mark_failed,
        mark_running_filter,
        mark_success,
        read_task_record,
        task_dir,
        update_task_record,
        write_json,
    )
except ImportError:  # pragma: no cover - direct script fallback.
    from config import (  # type: ignore
        API_PREFIX,
        FILTER_BASE_URL,
        FILTER_POLL_INTERVAL_SECONDS,
        FILTER_POLL_MAX_ATTEMPTS,
        FILTER_TIMEOUT_SECONDS,
        LESION_BASE_URL,
        LESION_POLL_INTERVAL_SECONDS,
        LESION_POLL_MAX_ATTEMPTS,
        LESION_REQUESTED_TYPES,
        LESION_SKIP_ON_SEVERE_ARTIFACT,
        HOST,
        LESION_SERVICE_ENABLED,
        LESION_TIMEOUT_SECONDS,
        MODULE_NAME,
        MODULE_VERSION,
        OUTPUT_ROOT,
        PORT,
        RAG_ENABLED,
    )
    from rag.db import health as rag_db_health  # type: ignore
    from rag.llm_provider import LlmProviderError  # type: ignore
    from rag.report_enhancer import ReportEnhancementError, enhance_report_assist  # type: ignore
    from rag.retriever import RagRetrievalError  # type: ignore
    from rag.clinical_assist import (  # type: ignore
        ClinicalAssistError,
        generate_consultation_assist,
        generate_diagnosis_assist,
    )
    from ai_imaging_readiness import build_ai_imaging_status  # type: ignore
    from dicom_ingest import (  # type: ignore
        DicomIngestError,
        is_supported_ct_upload,
        normalize_saved_upload,
        safe_original_name,
        save_upload_stream,
    )
    from service_clients.filter_client import FilterClient, HttpFilterClient  # type: ignore
    from service_clients.lesion_client import HttpLesionClient, LesionClient  # type: ignore
    from review_store import create_or_update_review, read_review  # type: ignore
    from task_store import (  # type: ignore
        api_error,
        create_task_record,
        mark_failed,
        mark_running_filter,
        mark_success,
        read_task_record,
        task_dir,
        update_task_record,
        write_json,
    )


class OrchestratorErrorCode:
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    DICOM_NORMALIZATION_FAILED = "DICOM_NORMALIZATION_FAILED"
    FILTER_UNAVAILABLE = "FILTER_UNAVAILABLE"
    FILTER_TASK_FAILED = "FILTER_TASK_FAILED"
    FILTER_TIMEOUT = "FILTER_TIMEOUT"
    RESULT_NOT_FOUND = "RESULT_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    ORCHESTRATION_FAILED = "ORCHESTRATION_FAILED"
    LESION_SERVICE_UNAVAILABLE = "LESION_SERVICE_UNAVAILABLE"
    LESION_TASK_FAILED = "LESION_TASK_FAILED"
    LESION_TIMEOUT = "LESION_TIMEOUT"
    INVALID_REVIEW_PAYLOAD = "INVALID_REVIEW_PAYLOAD"
    INVALID_REVIEW_STATUS = "INVALID_REVIEW_STATUS"
    TASK_NOT_SUCCESS = "TASK_NOT_SUCCESS"
    RAG_RETRIEVAL_FAILED = "RAG_RETRIEVAL_FAILED"
    LLM_PROVIDER_FAILED = "LLM_PROVIDER_FAILED"
    CLINICAL_ASSIST_FAILED = "CLINICAL_ASSIST_FAILED"


class FilterUnavailableError(RuntimeError):
    pass


class FilterTaskFailedError(RuntimeError):
    pass


class LesionUnavailableError(RuntimeError):
    pass


class LesionTaskFailedError(RuntimeError):
    pass


class LesionTimeoutError(TimeoutError):
    pass


@dataclass
class ServiceState:
    available: bool = True
    filter_base_url: str = FILTER_BASE_URL
    error: Optional[str] = None


filter_client: FilterClient = HttpFilterClient(FILTER_BASE_URL, FILTER_TIMEOUT_SECONDS)
lesion_client: LesionClient = HttpLesionClient(LESION_BASE_URL, LESION_TIMEOUT_SECONDS)
service_state = ServiceState()


def ensure_dirs() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def reliability_from_quality(severity: str) -> tuple[str, str]:
    if severity == "none":
        return "normal", "未检测到明显金属伪影。"
    if severity == "mild":
        return "slightly_limited_by_artifact", "存在轻度金属伪影，建议阅片时关注邻近区域。"
    if severity == "moderate":
        return "limited_by_artifact", "存在中度金属伪影，可能影响邻近区域判断。"
    return "strongly_limited_by_artifact", "存在重度金属伪影，可能明显影响局部结构判断。"


def warning_from_quality(severity: str) -> list[str]:
    if severity == "none":
        return []
    if severity == "mild":
        return ["存在轻度金属伪影，建议阅片时关注邻近区域。"]
    if severity == "moderate":
        return ["存在中度金属伪影，可能影响邻近区域判断。"]
    return ["存在重度金属伪影，AI 结果可信度可能明显受限。"]


def absolutize_preview_urls(preview_urls: dict[str, str]) -> dict[str, str]:
    return {key: filter_client.absolute_url(value) or value for key, value in preview_urls.items()}


def build_quality_context(filter_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_detected": filter_result.get("artifact_detected"),
        "artifact_ratio": filter_result.get("artifact_ratio"),
        "severity": filter_result.get("severity"),
        "affected_slices": filter_result.get("affected_slices", []),
        "artifact_segmentation": filter_result.get("artifact_segmentation") or {},
        "artifact_reduction": filter_result.get("artifact_reduction") or {},
        "analysis_reliability": reliability_from_quality(str(filter_result.get("severity") or "unknown"))[0],
    }


def should_skip_lesion_analysis(filter_result: dict[str, Any]) -> tuple[bool, str]:
    severity = str(filter_result.get("severity") or "unknown")
    if LESION_SKIP_ON_SEVERE_ARTIFACT and severity == "severe":
        return True, "存在重度金属伪影，配置要求跳过病灶识别。"
    return False, ""


def wait_lesion_success(lesion_task: dict[str, Any]) -> dict[str, Any]:
    current = lesion_task
    task_url = str(lesion_task.get("task_url") or "")
    for _ in range(LESION_POLL_MAX_ATTEMPTS):
        current = lesion_client.get_task(task_url)
        status = current.get("status")
        if status == "success":
            return current
        if status == "failed":
            error_code = current.get("error_code")
            error_message = current.get("error_message")
            if error_code and error_message:
                raise LesionTaskFailedError(f"{error_code}: {error_message}")
            raise LesionTaskFailedError(error_message or error_code or "Lesion task failed")
        time.sleep(LESION_POLL_INTERVAL_SECONDS)
    raise TimeoutError("Lesion task polling timeout")


def build_lesion_analysis_without_service() -> dict[str, Any]:
    return {
        "status": "not_configured",
        "enabled": False,
        "results": [],
        "warnings": [],
    }


def build_skipped_lesion_analysis(reason: str) -> dict[str, Any]:
    return {
        "status": "skipped",
        "enabled": True,
        "results": [],
        "warnings": [reason],
    }


def run_lesion_analysis(
    *,
    input_path: Path,
    original_filename: str,
    content_type: Optional[str],
    case_context: dict[str, Any],
    filter_result: dict[str, Any],
) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
    if not LESION_SERVICE_ENABLED:
        return build_lesion_analysis_without_service(), None

    skip, reason = should_skip_lesion_analysis(filter_result)
    if skip:
        return build_skipped_lesion_analysis(reason), None

    quality_context = build_quality_context(filter_result)
    try:
        lesion_task = lesion_client.create_task(
            input_path,
            original_filename,
            content_type,
            case_context,
            quality_context,
            LESION_REQUESTED_TYPES,
        )
    except Exception as exc:
        raise LesionUnavailableError(str(exc)) from exc

    try:
        lesion_task = wait_lesion_success(lesion_task)
    except TimeoutError as exc:
        raise LesionTimeoutError(str(exc)) from exc
    lesion_result = lesion_client.get_result(str(lesion_task.get("result_url")))
    lesion_analysis = {
        "status": "success",
        "enabled": True,
        "task_id": lesion_task.get("task_id"),
        "result_url": lesion_client.absolute_url(lesion_task.get("result_url")),
        "input_policy": lesion_result.get("input_policy", {}),
        "results": lesion_result.get("results", []),
        "summary": lesion_result.get("summary", {}),
        "warnings": lesion_result.get("warnings", []),
    }
    return lesion_analysis, lesion_result


def combine_report_assist(qc_suggestion: str, lesion_analysis: dict[str, Any], base_warnings: list[str]) -> dict[str, Any]:
    results = lesion_analysis.get("results") or []
    lesion_texts = [item.get("report_suggestion") for item in results if item.get("report_suggestion")]
    if lesion_analysis.get("status") == "not_configured":
        lesion_text = "未接入病灶识别模型。"
    elif lesion_analysis.get("status") == "skipped":
        lesion_text = "本次病灶识别已跳过。"
    elif lesion_texts:
        lesion_text = " ".join(lesion_texts)
    else:
        lesion_text = "病灶识别未返回明确提示。"
    warnings = list(dict.fromkeys(base_warnings + (lesion_analysis.get("warnings") or [])))
    limitations = ["AI 结果仅供辅助参考，最终结论需医生审核。"]
    recommended_actions = [{"code": "review_original_ct", "text": "建议医生结合原始 CT 影像复核。"}]
    if any("伪影" in warning for warning in warnings):
        recommended_actions.append({"code": "review_artifact_area", "text": "建议重点复核金属伪影邻近区域。"})
    return {
        "summary": f"{qc_suggestion} {lesion_text}",
        "quality_control_text": qc_suggestion,
        "lesion_text": lesion_text,
        "rag_enhanced": False,
        "suggested_report_sections": {
            "findings": [qc_suggestion, lesion_text],
            "impression": [lesion_text],
            "limitations": limitations,
        },
        "recommended_actions": recommended_actions,
        "rag_context": {
            "enabled": False,
            "status": "disabled",
            "retrieval_confidence": 0.0,
            "sources": [],
            "fallback_reason": None,
        },
        "llm_context": {
            "enabled": False,
            "provider": "rule_template",
            "model": None,
            "status": "disabled",
            "prompt_version": "report_assist_v1",
            "fallback_reason": None,
        },
        "suggestions": [],
        "warnings": warnings,
        "can_enter_report": lesion_analysis.get("status") == "success",
        "requires_doctor_review": True,
        "prohibited_claims": ["确诊", "排除", "无需复核", "自动完成诊断"],
    }


def build_orchestrator_result(
    *,
    task_id: str,
    original_filename: str,
    task_record: dict[str, Any],
    filter_task: dict[str, Any],
    filter_result: dict[str, Any],
    lesion_analysis: dict[str, Any],
    elapsed_ms: int,
) -> dict[str, Any]:
    input_metadata = filter_result.get("input_metadata") or {}
    severity = str(filter_result.get("severity") or "unknown")
    reliability, reliability_reason = reliability_from_quality(severity)
    qc_result_url = filter_client.absolute_url(filter_task.get("result_url") or filter_result.get("result_url"))
    qc_mask_url = filter_client.absolute_url(filter_task.get("mask_url") or filter_result.get("download_url"))
    qc_preview_urls = absolutize_preview_urls(filter_result.get("preview_urls") or {})
    artifact_reduction = dict(filter_result.get("artifact_reduction") or {})
    if artifact_reduction.get("corrected_ct_url"):
        artifact_reduction["corrected_ct_url"] = filter_client.absolute_url(artifact_reduction.get("corrected_ct_url"))
    qc_suggestion = filter_result.get("report_suggestion") or "建议医生结合原始影像复核。"
    warnings = warning_from_quality(severity)
    reduction_warning = artifact_reduction.get("warning")
    if reduction_warning and not artifact_reduction.get("use_for_lesion_input"):
        warnings.append(str(reduction_warning))
    warnings.append("AI 结果仅供辅助参考，最终结论需医生审核。")
    created_at = task_record.get("created_at")
    finished_at = time.strftime("%Y-%m-%dT%H:%M:%S")
    report_assist = combine_report_assist(qc_suggestion, lesion_analysis, warnings)
    if RAG_ENABLED:
        report_assist = enhance_report_assist(
            report_assist,
            {
                "artifact_detected": filter_result.get("artifact_detected"),
                "artifact_ratio": filter_result.get("artifact_ratio"),
                "severity": severity,
                "affected_slices": filter_result.get("affected_slices", []),
                "analysis_reliability": reliability,
            },
            lesion_analysis,
            task_record.get("case_context") or {},
        )

    quality_control = {
        "backend": filter_result.get("backend"),
        "artifact_detected": filter_result.get("artifact_detected"),
        "artifact_ratio": filter_result.get("artifact_ratio"),
        "severity": severity,
        "affected_slices": filter_result.get("affected_slices", []),
        "report_suggestion": qc_suggestion,
        "result_url": qc_result_url,
        "mask_url": qc_mask_url,
        "preview_urls": qc_preview_urls,
        "artifact_segmentation": filter_result.get("artifact_segmentation") or {},
        "artifact_reduction": artifact_reduction,
        "lesion_input_policy": lesion_analysis.get("input_policy") or {},
        "model_name": filter_result.get("model_name"),
        "model_version": filter_result.get("model_version"),
        "elapsed_ms": filter_result.get("elapsed_ms"),
    }
    ai_imaging_status = build_ai_imaging_status(
        quality_control=quality_control,
        lesion_analysis=lesion_analysis,
        report_assist=report_assist,
    )

    result = {
        "task_id": task_id,
        "status": "success",
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "case_context": task_record.get("case_context")
        or {
            "patient_id": None,
            "study_id": None,
            "series_id": None,
            "report_id": None,
            "doctor_id": None,
        },
        "pipeline": {
            "quality_control": "success",
            "lesion_analysis": lesion_analysis.get("status"),
            "report_assist": "success",
        },
        "input": {
            "file_name": original_filename,
            "source_format": (task_record.get("input_metadata") or {}).get("source_format"),
            "normalized_file": task_record.get("input_file"),
            "normalization": (task_record.get("input_metadata") or {}).get("normalization"),
            "image_size_xyz": input_metadata.get("image_size_xyz") or filter_result.get("shape"),
            "array_shape_zyx": input_metadata.get("array_shape_zyx") or filter_result.get("array_shape_zyx"),
            "spacing": input_metadata.get("spacing") or filter_result.get("spacing"),
        },
        "quality_control": quality_control,
        "ai_imaging_status": ai_imaging_status,
        "analysis_reliability": reliability,
        "reliability_reason": reliability_reason,
        "lesion_analysis": lesion_analysis,
        "report_assist": report_assist,
        "warnings": report_assist["warnings"],
        "created_at": created_at,
        "finished_at": finished_at,
        "elapsed_ms": elapsed_ms,
        "error_code": None,
        "error_message": None,
    }
    return result


def wait_filter_success(filter_task: dict[str, Any]) -> dict[str, Any]:
    current = filter_task
    task_url = str(filter_task.get("task_url") or "")
    for _ in range(FILTER_POLL_MAX_ATTEMPTS):
        current = filter_client.get_task(task_url)
        status = current.get("status")
        if status == "success":
            return current
        if status == "failed":
            raise FilterTaskFailedError(current.get("error_message") or current.get("error_code") or "Filter task failed")
        time.sleep(FILTER_POLL_INTERVAL_SECONDS)
    raise TimeoutError("Filter task polling timeout")


def classify_orchestration_error(exc: Exception) -> str:
    if isinstance(exc, FilterUnavailableError):
        return OrchestratorErrorCode.FILTER_UNAVAILABLE
    if isinstance(exc, FilterTaskFailedError):
        return OrchestratorErrorCode.FILTER_TASK_FAILED
    if isinstance(exc, LesionTimeoutError):
        return OrchestratorErrorCode.LESION_TIMEOUT
    if isinstance(exc, TimeoutError):
        return OrchestratorErrorCode.FILTER_TIMEOUT
    if isinstance(exc, LesionUnavailableError):
        return OrchestratorErrorCode.LESION_SERVICE_UNAVAILABLE
    if isinstance(exc, LesionTaskFailedError):
        return OrchestratorErrorCode.LESION_TASK_FAILED
    if isinstance(exc, RagRetrievalError):
        return OrchestratorErrorCode.RAG_RETRIEVAL_FAILED
    if isinstance(exc, (LlmProviderError, ReportEnhancementError)):
        return OrchestratorErrorCode.LLM_PROVIDER_FAILED
    return OrchestratorErrorCode.ORCHESTRATION_FAILED


def run_orchestration_task(task_id: str, input_path: Path, original_filename: str, content_type: Optional[str]) -> None:
    started = time.perf_counter()
    output_dir = task_dir(OUTPUT_ROOT, task_id)
    try:
        mark_running_filter(OUTPUT_ROOT, task_id)
        try:
            filter_task = filter_client.create_task(input_path, original_filename, content_type)
        except Exception as exc:
            raise FilterUnavailableError(str(exc)) from exc
        update_task_record(
            OUTPUT_ROOT,
            task_id,
            filter_task_id=filter_task.get("task_id"),
            filter_status=filter_task.get("status"),
        )
        filter_task = wait_filter_success(filter_task)
        task_record = update_task_record(
            OUTPUT_ROOT,
            task_id,
            status="filter_success",
            filter_task_id=filter_task.get("task_id"),
            filter_status=filter_task.get("status"),
        )
        filter_result = filter_client.get_result(str(filter_task.get("result_url")))
        write_json(output_dir / "filter_result.json", filter_result)
        lesion_analysis, lesion_result = run_lesion_analysis(
            input_path=input_path,
            original_filename=original_filename,
            content_type=content_type,
            case_context=task_record.get("case_context") or {},
            filter_result=filter_result,
        )
        if lesion_result is not None:
            write_json(output_dir / "lesion_result.json", lesion_result)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        orchestrator_result = build_orchestrator_result(
            task_id=task_id,
            original_filename=original_filename,
            task_record=task_record,
            filter_task=filter_task,
            filter_result=filter_result,
            lesion_analysis=lesion_analysis,
            elapsed_ms=elapsed_ms,
        )
        write_json(output_dir / "orchestrator_result.json", orchestrator_result)
        mark_success(OUTPUT_ROOT, task_id, elapsed_ms)
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        mark_failed(OUTPUT_ROOT, task_id, classify_orchestration_error(exc), str(exc), elapsed_ms)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_dirs()
    yield


async def http_exception_handler(_: Any, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "failed", "error_code": f"HTTP_{exc.status_code}", "message": str(exc.detail)},
    )


app = FastAPI(title="头部 CT AI 影像分析编排服务", version=MODULE_VERSION, lifespan=lifespan)
app.add_exception_handler(HTTPException, http_exception_handler)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "module": MODULE_NAME,
        "health": f"{API_PREFIX}/health",
        "tasks": f"{API_PREFIX}/tasks",
        "docs": "/docs",
    }


@app.get(f"{API_PREFIX}/health")
async def health():
    try:
        filter_health = filter_client.health()
        service_state.available = True
        service_state.error = None
    except Exception as exc:
        filter_health = {"status": "unavailable", "error": str(exc)}
        service_state.available = False
        service_state.error = str(exc)
    if LESION_SERVICE_ENABLED:
        try:
            lesion_health = lesion_client.health()
        except Exception as exc:
            lesion_health = {"status": "unavailable", "error": str(exc)}
    else:
        lesion_health = {"status": "not_configured"}
    return {
        "status": "ok" if service_state.available else "degraded",
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "service": asdict(service_state),
        "filter": filter_health,
        "lesion": lesion_health,
        "lesion_service_enabled": LESION_SERVICE_ENABLED,
        "rag": {
            "enabled": RAG_ENABLED,
            "vector_db": rag_db_health() if RAG_ENABLED else {"status": "disabled", "backend": "pgvector"},
        },
        "storage": {
            "outputs": str(OUTPUT_ROOT.resolve()),
            "outputs_exists": OUTPUT_ROOT.exists(),
        },
    }


@app.post(f"{API_PREFIX}/tasks")
async def create_head_ct_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    study_id: Optional[str] = Form(None),
    series_id: Optional[str] = Form(None),
    report_id: Optional[str] = Form(None),
    doctor_id: Optional[str] = Form(None),
):
    if not is_supported_ct_upload(file.filename or ""):
        raise api_error(400, OrchestratorErrorCode.INVALID_FILE_TYPE, "只支持 .nii、.nii.gz、.dcm、.dicom 或 DICOM .zip 格式的 CT 文件")
    ensure_dirs()
    task_id = uuid.uuid4().hex
    original_filename = safe_original_name(file.filename)
    output_dir = task_dir(OUTPUT_ROOT, task_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = output_dir / "source" / original_filename
    try:
        save_upload_stream(file.file, source_path)
        try:
            normalized = normalize_saved_upload(original_filename, source_path, output_dir, file.content_type)
        except DicomIngestError as exc:
            raise api_error(400, OrchestratorErrorCode.DICOM_NORMALIZATION_FAILED, str(exc)) from exc
        task = create_task_record(
            output_root=OUTPUT_ROOT,
            task_id=task_id,
            original_file=original_filename,
            input_file=normalized.input_filename,
            input_metadata=normalized.metadata,
            case_context={
                "patient_id": patient_id,
                "study_id": study_id,
                "series_id": series_id,
                "report_id": report_id,
                "doctor_id": doctor_id,
            },
        )
        background_tasks.add_task(
            run_orchestration_task,
            task_id,
            normalized.input_path,
            normalized.input_filename,
            "application/octet-stream",
        )
        return task
    finally:
        try:
            await file.close()
        except Exception:
            pass


@app.get(f"{API_PREFIX}/tasks/{{task_id}}")
async def get_head_ct_task(task_id: str):
    return read_task_record(OUTPUT_ROOT, task_id)


@app.get(f"{API_PREFIX}/results/{{task_id}}")
async def get_head_ct_result(task_id: str):
    path = task_dir(OUTPUT_ROOT, task_id) / "orchestrator_result.json"
    if not path.exists():
        raise api_error(404, OrchestratorErrorCode.RESULT_NOT_FOUND, "编排结果不存在")
    return FileResponse(path, media_type="application/json", filename=path.name)


@app.post(f"{API_PREFIX}/clinical/consultation")
async def create_clinical_consultation(payload: dict[str, Any]):
    try:
        return generate_consultation_assist(payload)
    except ClinicalAssistError as exc:
        raise api_error(502, OrchestratorErrorCode.CLINICAL_ASSIST_FAILED, str(exc)) from exc


@app.post(f"{API_PREFIX}/clinical/diagnosis")
async def create_clinical_diagnosis(payload: dict[str, Any]):
    try:
        return generate_diagnosis_assist(payload)
    except ClinicalAssistError as exc:
        raise api_error(502, OrchestratorErrorCode.CLINICAL_ASSIST_FAILED, str(exc)) from exc

@app.post(f"{API_PREFIX}/reviews/{{task_id}}")
async def create_head_ct_review(task_id: str, payload: dict[str, Any]):
    review = create_or_update_review(OUTPUT_ROOT, task_id, payload)
    return {"status": "success", "review": review}


@app.get(f"{API_PREFIX}/reviews/{{task_id}}")
async def get_head_ct_review(task_id: str):
    review = read_review(OUTPUT_ROOT, task_id)
    return {"status": "success", "review": review}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("OrchestratorServer:app", host=HOST, port=PORT, reload=False)
