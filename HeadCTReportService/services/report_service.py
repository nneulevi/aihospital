"""Clinical report workflow and Orchestrator result mapping."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from ..config import DEPLOYMENT_MODE
from ..exceptions import ReportServiceError, forbidden
from ..repositories.report_repository import PostgresReportRepository
from ..service_clients.emr_client import EmrClient
from ..service_clients.orchestrator_client import OrchestratorClient


ROLE_PERMISSIONS = {
    "technician": {"register_examination", "create_report", "read"},
    "reporting_doctor": {"create_report", "read", "edit", "submit_review"},
    "reviewing_doctor": {"read", "approve", "request_revision"},
    "signing_doctor": {"read", "edit", "submit_review", "sign", "release", "amend"},
    "administrator": {"register_examination", "create_report", "read", "edit", "submit_review", "dispatch"},
    "integration_service": {"register_examination", "create_report", "read", "release", "dispatch"},
}


def require_permission(actor: dict[str, str], permission: str) -> None:
    if permission not in ROLE_PERMISSIONS.get(actor.get("role", ""), set()):
        raise forbidden("REVIEW_PERMISSION_DENIED", f"角色 {actor.get('role')} 无权执行 {permission}")


def join_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str) and item.strip():
                parts.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("description")
                if text:
                    parts.append(str(text).strip())
        return "\n".join(parts)
    return ""


def stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def extract_model_versions(result: dict[str, Any]) -> dict[str, Any]:
    quality = result.get("quality_control") or {}
    lesion = result.get("lesion_analysis") or {}
    lesion_models = []
    for item in lesion.get("results") or []:
        lesion_models.append(
            {
                "lesion_type": item.get("lesion_type"),
                "model_name": item.get("model_name"),
                "model_version": item.get("model_version"),
            }
        )
    return {
        "orchestrator": result.get("module_version"),
        "quality_control": {
            "model_name": quality.get("model_name"),
            "model_version": quality.get("model_version"),
            "backend": quality.get("backend"),
        },
        "lesion_models": lesion_models,
    }


def draft_sections(result: dict[str, Any]) -> dict[str, str]:
    assist = result.get("report_assist") or {}
    sections = assist.get("suggested_report_sections") or {}
    findings = join_text(sections.get("findings")) or join_text(assist.get("quality_control_text"))
    impression = join_text(sections.get("impression")) or join_text(assist.get("lesion_text"))
    recommendations = join_text(assist.get("recommended_actions"))
    limitations = join_text(sections.get("limitations"))
    warnings = join_text(assist.get("warnings") or result.get("warnings"))
    if limitations:
        recommendations = "\n".join(filter(None, [recommendations, "局限性：" + limitations]))
    if warnings:
        recommendations = "\n".join(filter(None, [recommendations, "注意事项：" + warnings]))
    return {
        "findings": findings or "AI 未生成可用影像所见，请医生结合原始影像填写。",
        "impression": impression or "AI 未生成可用诊断意见，请医生审核后填写。",
        "recommendations": recommendations or "AI 结果仅供辅助参考，最终结论需医生审核。",
    }


SEVERITY_TEXT = {
    "none": "未见明确金属伪影",
    "mild": "轻度金属伪影",
    "moderate": "中度金属伪影",
    "severe": "重度金属伪影",
    "unknown": "伪影程度未明确",
}


def _format_slice_text(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (list, tuple)) and value:
        numbers = [int(item) for item in value if isinstance(item, (int, float)) or str(item).isdigit()]
        if numbers:
            numbers = sorted(set(numbers))
            if len(numbers) == 2 and numbers[0] != numbers[1]:
                return f"第{numbers[0]}-{numbers[1]}层"
            if len(numbers) > 2 and numbers == list(range(numbers[0], numbers[-1] + 1)):
                return f"第{numbers[0]}-{numbers[-1]}层"
            return "第" + "、".join(str(item) for item in numbers) + "层"
    return "模型未返回明确层面"


def _format_confidence(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "未返回"


def render_structured_sections(assist: dict[str, Any]) -> dict[str, str]:
    structured = assist.get("structured_findings")
    if not isinstance(structured, dict):
        return {}

    quality = structured.get("quality") or {}
    lesions = structured.get("lesions") or []
    review_focus = structured.get("review_focus") or []
    severity = quality.get("artifact_severity")
    severity_text = quality.get("artifact_severity_label") or SEVERITY_TEXT.get(
        str(severity or "unknown"),
        str(severity or "伪影程度未明确"),
    )
    affected_slices = quality.get("affected_slices_text") or _format_slice_text(quality.get("affected_slices"))

    findings = [
        "影像质量评估",
        f"- 本次头部 CT 图像质量提示：{severity_text}；受影响层面：{affected_slices}。",
        f"- 质量影响说明：{quality.get('interpretation') or '建议结合原始图像与相邻层面复核。'}",
        "",
        "AI检出结果",
    ]
    impression = ["诊断辅助意见"]
    if lesions:
        for lesion in lesions:
            location = lesion.get("location") or "模型未返回明确部位"
            slice_text = lesion.get("slice_range_text") or _format_slice_text(lesion.get("slice_range"))
            confidence = _format_confidence(lesion.get("confidence"))
            detected = "疑似阳性检出" if lesion.get("detected") else "未提示明确阳性检出"
            findings.append(
                f"- {lesion.get('lesion_type') or 'unknown'}：{detected}；部位：{location}；层面：{slice_text}；置信度{confidence}。"
            )
            findings.append(f"- 检出依据：{lesion.get('evidence') or '模型未返回可解释征象描述。'}")
            if lesion.get("detected"):
                impression.append(f"- AI辅助分析提示{location}存在疑似异常征象，建议重点复核{slice_text}及相邻层面。")
            else:
                impression.append("- AI辅助分析未提示明确阳性征象；如临床表现与影像不一致，仍建议结合原始图像复核。")
    else:
        findings.append("- 病灶模型未返回可结构化的检出项。")
        impression.append("- 当前 AI 结果不足以形成明确辅助倾向，请医生完成原始影像判读。")

    recommendations = [
        "建议与局限性",
        "- AI 结果仅供辅助参考，最终结论需医生审核。",
        "- confidence 表示模型置信度，不代表临床最终判断概率。",
    ]
    for focus in review_focus:
        recommendations.append(f"- {focus}")
    return {
        "findings": "\n".join(findings),
        "impression": "\n".join(impression),
        "recommendations": "\n".join(recommendations),
    }


def draft_sections(result: dict[str, Any]) -> dict[str, str]:
    assist = result.get("report_assist") or {}
    structured_sections = render_structured_sections(assist)
    sections = assist.get("suggested_report_sections") or {}
    findings = structured_sections.get("findings") or join_text(sections.get("findings")) or join_text(assist.get("quality_control_text"))
    impression = structured_sections.get("impression") or join_text(sections.get("impression")) or join_text(assist.get("lesion_text"))
    recommendations = join_text(assist.get("recommended_actions"))
    if structured_sections.get("recommendations"):
        recommendations = "\n".join(filter(None, [structured_sections["recommendations"], recommendations]))
    limitations = join_text(sections.get("limitations"))
    warnings = join_text(assist.get("warnings") or result.get("warnings"))
    if limitations:
        recommendations = "\n".join(filter(None, [recommendations, "局限性：" + limitations]))
    if warnings:
        recommendations = "\n".join(filter(None, [recommendations, "注意事项：" + warnings]))
    return {
        "findings": findings or "AI 未生成可用影像所见，请医生结合原始影像填写。",
        "impression": impression or "AI 未生成可用诊断意见，请医生审核后填写。",
        "recommendations": recommendations or "AI 结果仅供辅助参考，最终结论需医生审核。",
    }


class ReportService:
    def __init__(
        self,
        repository: PostgresReportRepository,
        orchestrator: OrchestratorClient,
        emr: EmrClient,
    ) -> None:
        self.repository = repository
        self.orchestrator = orchestrator
        self.emr = emr

    def register_examination(self, payload: dict[str, Any], actor: dict[str, str]) -> dict[str, Any]:
        require_permission(actor, "register_examination")
        return self.repository.register_examination(payload, actor)

    def create_report_from_analysis(
        self,
        *,
        task_id: str,
        examination: dict[str, Any],
        actor: dict[str, str],
        idempotency_key: Optional[str],
        request_id: Optional[str],
        client_ip: Optional[str],
    ) -> dict[str, Any]:
        require_permission(actor, "create_report")
        existing = self.repository.find_by_task_or_idempotency(task_id, idempotency_key)
        if existing:
            return existing
        result = self.orchestrator.get_completed_result(task_id)
        context = result.get("case_context") or {}
        if context.get("study_id") and context["study_id"] != examination["study_id"]:
            raise ReportServiceError("EXAMINATION_ID_MISMATCH", "AI 任务 study_id 与检查记录不一致", 409)
        if context.get("patient_id") and context["patient_id"] != examination["patient_id"]:
            raise ReportServiceError("EXAMINATION_ID_MISMATCH", "AI 任务 patient_id 与检查记录不一致", 409)
        assist = result.get("report_assist")
        if not isinstance(assist, dict):
            raise ReportServiceError("ANALYSIS_RESULT_INVALID", "AI 分析结果缺少 report_assist", 422)
        snapshot = {
            "orchestrator_task_id": task_id,
            "pipeline_version": result.get("module_version"),
            "model_versions": extract_model_versions(result),
            "quality_control": result.get("quality_control") or {},
            "lesion_analysis": result.get("lesion_analysis") or {},
            "report_assist": assist,
            "rag_references": (assist.get("rag_context") or {}).get("sources") or [],
            "source_result_hash": stable_hash(result),
            "deployment_mode": DEPLOYMENT_MODE,
        }
        return self.repository.create_from_analysis(
            examination=examination,
            snapshot=snapshot,
            report={"assigned_doctor_id": examination.get("assigned_doctor_id")},
            version=draft_sections(result),
            actor=actor,
            idempotency_key=idempotency_key,
            request_id=request_id,
            client_ip=client_ip,
        )

    def bind_analysis(
        self,
        study_id: str,
        task_id: str,
        assigned_doctor_id: Optional[str],
        actor: dict[str, str],
        idempotency_key: Optional[str],
        request_id: Optional[str],
        client_ip: Optional[str],
    ) -> dict[str, Any]:
        examination = self.repository.find_examination_by_study(study_id)
        examination["assigned_doctor_id"] = assigned_doctor_id
        return self.create_report_from_analysis(
            task_id=task_id,
            examination=examination,
            actor=actor,
            idempotency_key=idempotency_key,
            request_id=request_id,
            client_ip=client_ip,
        )

    def get_report(self, report_id: str, actor: dict[str, str]) -> dict[str, Any]:
        require_permission(actor, "read")
        return self.repository.get_report(report_id)

    def list_reports(self, actor: dict[str, str], **filters: Any) -> list[dict[str, Any]]:
        require_permission(actor, "read")
        return self.repository.list_reports(**filters)

    def edit_report(self, report_id: str, payload: dict[str, Any], actor: dict[str, str], **audit: Any) -> dict[str, Any]:
        require_permission(actor, "edit")
        return self.repository.update_draft(report_id, payload, actor, audit.get("request_id"), audit.get("client_ip"))

    def submit_review(self, report_id: str, actor: dict[str, str], **audit: Any) -> dict[str, Any]:
        require_permission(actor, "submit_review")
        return self.repository.transition(
            report_id, expected_statuses={"draft", "revision_required", "amendment_draft"},
            target_status="pending_review", actor=actor, action="report_submitted_for_review", **audit,
        )

    def approve(self, report_id: str, comment: Optional[str], actor: dict[str, str], **audit: Any) -> dict[str, Any]:
        require_permission(actor, "approve")
        return self.repository.transition(
            report_id, expected_statuses={"pending_review"}, target_status="approved", actor=actor,
            action="report_approved", decision="approved", comment=comment, **audit,
        )

    def request_revision(self, report_id: str, comment: Optional[str], actor: dict[str, str], **audit: Any) -> dict[str, Any]:
        require_permission(actor, "request_revision")
        if not comment:
            raise ReportServiceError("REVIEW_COMMENT_REQUIRED", "退回修订时必须填写审核意见", 422)
        return self.repository.transition(
            report_id, expected_statuses={"pending_review"}, target_status="revision_required", actor=actor,
            action="revision_requested", decision="revision_required", comment=comment, **audit,
        )

    def sign(self, report_id: str, actor: dict[str, str], **audit: Any) -> dict[str, Any]:
        require_permission(actor, "sign")
        return self.repository.transition(
            report_id, expected_statuses={"approved"}, target_status="signed", actor=actor,
            action="report_signed", **audit,
        )

    def release(self, report_id: str, actor: dict[str, str], **audit: Any) -> dict[str, Any]:
        require_permission(actor, "release")
        return self.repository.transition(
            report_id, expected_statuses={"signed"}, target_status="released", actor=actor,
            action="report_released", **audit,
        )

    def amend(self, report_id: str, payload: dict[str, Any], actor: dict[str, str], **audit: Any) -> dict[str, Any]:
        require_permission(actor, "amend")
        return self.repository.create_amendment(
            report_id, payload, actor, audit.get("request_id"), audit.get("client_ip")
        )

    def dispatch_outbox(self, actor: dict[str, str], limit: int = 20) -> dict[str, int]:
        require_permission(actor, "dispatch")
        delivered = 0
        failed = 0
        for event in self.repository.pending_outbox(limit):
            try:
                external_id = self.emr.push_report(event["payload_json"], str(event["id"]))
                self.repository.mark_outbox_delivered(str(event["id"]), str(event["report_id"]), external_id)
                delivered += 1
            except Exception as exc:
                self.repository.mark_outbox_failed(str(event["id"]), str(exc))
                failed += 1
        return {"delivered": delivered, "failed": failed}
