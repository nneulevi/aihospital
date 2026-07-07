"""Project-level readiness summary for the Head CT AI imaging workflow."""

from __future__ import annotations

from typing import Any


def _bool(value: Any) -> bool:
    return bool(value) if value is not None else False


def _first_result(lesion_analysis: dict[str, Any]) -> dict[str, Any]:
    results = lesion_analysis.get("results") or []
    return results[0] if results and isinstance(results[0], dict) else {}


def build_ai_imaging_status(
    *,
    quality_control: dict[str, Any],
    lesion_analysis: dict[str, Any],
    report_assist: dict[str, Any],
) -> dict[str, Any]:
    """Build a stable, front-end friendly status for project demo use.

    This is intentionally a project acceptance summary rather than a medical
    regulatory readiness claim. It tells the main platform what the AI chain
    actually did and which parts are classification, segmentation, correction,
    or human-reviewed report assistance.
    """

    artifact_reduction = quality_control.get("artifact_reduction") or {}
    lesion_policy = quality_control.get("lesion_input_policy") or {}
    lesion_result = _first_result(lesion_analysis)

    qc_ready = bool(quality_control.get("backend") and quality_control.get("model_name"))
    lesion_ready = lesion_analysis.get("status") == "success" and bool(lesion_analysis.get("results"))
    report_ready = _bool(report_assist.get("can_enter_report"))
    workflow_ready = qc_ready and lesion_ready and report_ready

    correction_executable = _bool(artifact_reduction.get("executable"))
    correction_registered = _bool(artifact_reduction.get("registered"))
    if correction_executable:
        reduction_status = "executable"
    elif correction_registered:
        reduction_status = "registered_not_executable"
    else:
        reduction_status = "not_configured"

    outputs_segmentation = bool(lesion_result.get("mask_url") or lesion_result.get("bbox"))
    lesion_task_type = "segmentation" if outputs_segmentation else "classification"
    lesion_fallback_used = any(
        bool(item.get("checkpoint_fallback_used"))
        for item in (lesion_analysis.get("results") or [])
        if isinstance(item, dict)
    )

    limitations: list[str] = []
    if reduction_status != "executable":
        limitations.append("metal_artifact_reduction_not_executed")
    if lesion_fallback_used:
        limitations.append("lesion_checkpoint_fallback_used")
    if not workflow_ready:
        limitations.append("workflow_not_fully_ready")

    return {
        "project_use_status": "ready_for_project_demo" if workflow_ready else "degraded_for_project_demo",
        "scope": "course_project_ai_assist",
        "workflow_ready": workflow_ready,
        "supported_workflow": [
            "ct_upload_to_artifact_segmentation",
            "ct_upload_to_lesion_classification",
            "ct_upload_to_report_assist",
            "doctor_review_to_final_report",
        ],
        "quality_control_model": {
            "status": "ready" if qc_ready else "not_ready",
            "task_type": "metal_artifact_segmentation",
            "backend": quality_control.get("backend"),
            "model_name": quality_control.get("model_name"),
            "model_version": quality_control.get("model_version"),
        },
        "artifact_reduction": {
            "status": reduction_status,
            "model_name": artifact_reduction.get("model_name"),
            "correction_status": artifact_reduction.get("correction_status"),
            "corrected_ct_used_for_lesion": _bool(lesion_policy.get("corrected_ct_used")),
            "lesion_input": lesion_policy.get("used_input") or "unknown",
        },
        "lesion_model": {
            "status": "ready" if lesion_ready else str(lesion_analysis.get("status") or "not_ready"),
            "task_type": lesion_task_type,
            "scope_note": "classification_result_without_segmentation_mask" if lesion_task_type == "classification" else "segmentation_output_available",
            "model_name": lesion_result.get("model_name"),
            "provider": lesion_result.get("provider"),
            "checkpoint_provenance": lesion_result.get("checkpoint_provenance"),
            "checkpoint_fallback_used": lesion_fallback_used,
            "outputs_segmentation": outputs_segmentation,
            "highest_confidence": (lesion_analysis.get("summary") or {}).get("highest_confidence")
            or lesion_result.get("confidence"),
        },
        "report_assist": {
            "status": "ready" if report_ready else "not_ready",
            "rag_enhanced": _bool(report_assist.get("rag_enhanced")),
            "requires_doctor_review": _bool(report_assist.get("requires_doctor_review")),
        },
        "diagnosis_output_policy": {
            "ai_role": "assistive_structured_analysis",
            "final_diagnosis_owner": "doctor",
            "autonomous_diagnosis": False,
        },
        "limitations": limitations,
    }
