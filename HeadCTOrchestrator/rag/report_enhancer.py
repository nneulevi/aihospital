"""Build RAG-enhanced report assistance from structured model outputs."""

from __future__ import annotations

from typing import Any

from .config import RAG_ENABLED
from .llm_provider import generate_report_assist_with_llm
from .retriever import retrieve_context
from .safety_rules import FORBIDDEN_TERMS, REVIEW_HINT, validate_report_safety


def build_query_text(quality_control: dict[str, Any], lesion_analysis: dict[str, Any]) -> tuple[str, list[str]]:
    severity = str(quality_control.get("severity") or "unknown")
    terms = ["head_ct", "report", "doctor_review", severity]
    tags = ["head_ct", "report"]
    if severity not in {"none", "unknown"}:
        terms.extend(["metal_artifact", "limited_by_artifact"])
        tags.append("artifact")
    for item in lesion_analysis.get("results") or []:
        lesion_type = str(item.get("lesion_type") or "")
        if lesion_type:
            terms.append(lesion_type)
            if "hemorrhage" in lesion_type:
                tags.append("hemorrhage")
        terms.append("positive" if item.get("detected") else "negative")
    return " ".join(terms), sorted(set(tags))


def disabled_context() -> dict[str, Any]:
    return {
        "enabled": False,
        "status": "disabled",
        "retrieval_confidence": 0.0,
        "sources": [],
        "fallback_reason": None,
    }


def disabled_llm_context() -> dict[str, Any]:
    return {
        "enabled": False,
        "provider": "rule_template",
        "model": None,
        "status": "disabled",
        "prompt_version": "report_assist_v1",
        "fallback_reason": None,
    }


class ReportEnhancementError(RuntimeError):
    pass


SEVERITY_LABELS = {
    "none": "未见明确金属伪影",
    "mild": "轻度金属伪影",
    "moderate": "中度金属伪影",
    "severe": "重度金属伪影",
    "unknown": "伪影程度未明确",
}


def _format_slices(value: Any) -> str:
    if value in (None, "", []):
        return "模型未返回明确层面"
    if isinstance(value, (list, tuple)):
        numbers = [int(item) for item in value if isinstance(item, (int, float)) or str(item).isdigit()]
        if not numbers:
            return "模型未返回明确层面"
        numbers = sorted(set(numbers))
        if len(numbers) == 2 and numbers[0] != numbers[1]:
            return f"第{numbers[0]}-{numbers[1]}层"
        if len(numbers) > 2 and numbers == list(range(numbers[0], numbers[-1] + 1)):
            return f"第{numbers[0]}-{numbers[-1]}层"
        return "第" + "、".join(str(item) for item in numbers) + "层"
    return str(value)


def _confidence(value: Any) -> float | None:
    try:
        if value is None:
            return None
        score = float(value)
    except (TypeError, ValueError):
        return None
    return round(min(max(score, 0.0), 1.0), 3)


def _build_structured_findings(quality_control: dict[str, Any], lesion_analysis: dict[str, Any]) -> dict[str, Any]:
    severity = str(quality_control.get("severity") or "unknown")
    affected_slices = quality_control.get("affected_slices") or quality_control.get("artifact_slices") or []
    structured: dict[str, Any] = {
        "quality": {
            "artifact_detected": bool(quality_control.get("artifact_detected") or severity not in {"none", "unknown"}),
            "artifact_severity": severity,
            "artifact_severity_label": SEVERITY_LABELS.get(severity, severity),
            "affected_slices": affected_slices,
            "affected_slices_text": _format_slices(affected_slices),
            "artifact_ratio": quality_control.get("artifact_ratio"),
            "interpretation": (
                "伪影邻近区域的细小高密度影、边界和脑实质结构判断可靠性可能下降。"
                if severity in {"moderate", "severe"}
                else "伪影对整体判读影响相对有限，但邻近层面仍建议人工复核。"
            ),
        },
        "lesions": [],
        "review_focus": [],
    }

    for item in lesion_analysis.get("results") or []:
        raw_slices = item.get("slice_range") or item.get("slices") or item.get("slice_indices")
        lesion = {
            "lesion_type": item.get("lesion_type") or "unknown",
            "detected": bool(item.get("detected")),
            "confidence": _confidence(item.get("confidence")),
            "location": item.get("location") or item.get("anatomy") or item.get("region") or "模型未返回明确部位",
            "slice_range": raw_slices or [],
            "slice_range_text": _format_slices(raw_slices),
            "evidence": item.get("evidence")
            or item.get("report_suggestion")
            or "模型仅返回分类结果，未提供可解释征象描述。",
            "model_name": item.get("model_name"),
            "model_version": item.get("model_version"),
        }
        structured["lesions"].append(lesion)
        structured["review_focus"].append(
            f"重点复核{lesion['slice_range_text']} {lesion['location']}，并与伪影邻近区域及相邻层面对照。"
        )

    if not structured["lesions"]:
        structured["review_focus"].append("病灶模型未返回可结构化的检出项，建议医生结合原始影像完成判读。")
    return structured


def _professional_sections(structured: dict[str, Any]) -> tuple[list[str], list[str], list[str], list[dict[str, str]]]:
    quality = structured.get("quality") or {}
    lesions = structured.get("lesions") or []
    findings = [
        (
            "影像质量评估："
            f"{quality.get('artifact_severity_label', '伪影程度未明确')}，"
            f"受影响层面：{quality.get('affected_slices_text', '模型未返回明确层面')}；"
            f"{quality.get('interpretation', '')}"
        )
    ]
    impression: list[str] = []
    limitations = ["模型输出为辅助分析结果，confidence 表示模型置信度，不代表临床最终判断概率。"]
    actions = [{"code": "review_original_ct", "text": "请医生结合原始 CT 图像、窗宽窗位及相邻层面复核。"}]

    if lesions:
        for lesion in lesions:
            confidence = lesion.get("confidence")
            confidence_text = f"置信度{confidence:.2f}" if isinstance(confidence, float) else "置信度未返回"
            detected_text = "疑似阳性检出" if lesion.get("detected") else "未提示明确阳性检出"
            findings.append(
                "AI检出结果："
                f"{lesion.get('lesion_type', 'unknown')} {detected_text}，"
                f"部位：{lesion.get('location')}，层面：{lesion.get('slice_range_text')}，"
                f"{confidence_text}；检出依据：{lesion.get('evidence')}"
            )
            if lesion.get("detected"):
                impression.append(
                    "诊断辅助意见："
                    f"AI辅助分析提示{lesion.get('location')}存在疑似异常征象，"
                    f"请重点复核{lesion.get('slice_range_text')}及相邻层面。"
                )
            else:
                impression.append("诊断辅助意见：AI辅助分析未提示明确阳性征象；如临床症状与影像不一致，仍建议结合原始图像复核。")
    else:
        findings.append("AI检出结果：病灶模型未返回可结构化的检出项。")
        impression.append("诊断辅助意见：当前 AI 结果不足以形成明确辅助倾向，请医生完成原始影像判读。")

    for focus in structured.get("review_focus") or []:
        actions.append({"code": "review_focus", "text": str(focus)})
    limitations.append(REVIEW_HINT)
    return findings, impression, limitations, actions


def _merge_rule_template(
    base_report_assist: dict[str, Any],
    retrieval: dict[str, Any],
    quality_control: dict[str, Any],
    lesion_analysis: dict[str, Any],
) -> dict[str, Any]:
    enhanced = dict(base_report_assist)
    findings = list(enhanced.get("suggested_report_sections", {}).get("findings", []))
    impression = list(enhanced.get("suggested_report_sections", {}).get("impression", []))
    limitations = list(enhanced.get("suggested_report_sections", {}).get("limitations", []))
    if retrieval.get("snippets"):
        findings.append("已检索项目知识库用于报告辅助表达，引用来源见 rag_context.sources。")
    if quality_control.get("severity") in {"moderate", "severe"}:
        limitations.append("局部结构判断可能受金属伪影影响，建议医生重点复核受影响区域。")
    if lesion_analysis.get("status") == "success":
        impression.append("病灶识别结果仅作为报告草稿辅助，需结合原始影像确认。")
    limitations.append(REVIEW_HINT)
    enhanced["suggested_report_sections"] = {
        "findings": list(dict.fromkeys(findings)),
        "impression": list(dict.fromkeys(impression)),
        "limitations": list(dict.fromkeys(limitations)),
    }
    actions = list(enhanced.get("recommended_actions") or [])
    if retrieval.get("sources"):
        actions.append({"code": "manual_report_review", "text": "建议医生结合 RAG 引用来源复核报告草稿。"})
    enhanced["recommended_actions"] = list({item["code"]: item for item in actions if item.get("code")}.values())
    return enhanced


def _merge_rule_template(
    base_report_assist: dict[str, Any],
    retrieval: dict[str, Any],
    quality_control: dict[str, Any],
    lesion_analysis: dict[str, Any],
) -> dict[str, Any]:
    enhanced = dict(base_report_assist)
    structured = _build_structured_findings(quality_control, lesion_analysis)
    enhanced["structured_findings"] = structured
    professional_findings, professional_impression, professional_limitations, professional_actions = _professional_sections(structured)

    sections = enhanced.get("suggested_report_sections") or {}
    findings = professional_findings + list(sections.get("findings", []))
    impression = professional_impression + list(sections.get("impression", []))
    limitations = professional_limitations + list(sections.get("limitations", []))

    if retrieval.get("snippets"):
        findings.append("已检索项目知识库用于报告辅助表达，引用来源见 rag_context.sources。")
    if quality_control.get("severity") in {"moderate", "severe"}:
        limitations.append("局部结构判断可能受金属伪影影响，建议医生重点复核受影响区域。")
    if lesion_analysis.get("status") == "success":
        impression.append("病灶识别结果仅作为报告草稿辅助，需结合原始影像确认。")

    enhanced["suggested_report_sections"] = {
        "findings": list(dict.fromkeys(findings)),
        "impression": list(dict.fromkeys(impression)),
        "limitations": list(dict.fromkeys(limitations)),
    }

    actions = professional_actions + list(enhanced.get("recommended_actions") or [])
    if retrieval.get("sources"):
        actions.append({"code": "manual_report_review", "text": "建议医生结合 RAG 引用来源复核报告草稿。"})
    enhanced["recommended_actions"] = list({item["code"]: item for item in actions if item.get("code")}.values())
    return enhanced


def enhance_report_assist(
    base_report_assist: dict[str, Any],
    quality_control: dict[str, Any],
    lesion_analysis: dict[str, Any],
    case_context: dict[str, Any],
) -> dict[str, Any]:
    enhanced = dict(base_report_assist)
    if not RAG_ENABLED:
        enhanced["rag_enhanced"] = False
        enhanced.setdefault("rag_context", disabled_context())
        enhanced.setdefault("llm_context", disabled_llm_context())
        enhanced = _merge_rule_template(enhanced, {"sources": [], "snippets": []}, quality_control, lesion_analysis)
        enhanced, _ = validate_report_safety(enhanced)
        return enhanced

    query_text, filter_tags = build_query_text(quality_control, lesion_analysis)
    retrieval = retrieve_context(query_text, filter_tags=filter_tags)
    rag_context = {
        "enabled": True,
        "status": retrieval.get("status"),
        "retrieval_confidence": retrieval.get("retrieval_confidence", 0.0),
        "query_terms": query_text.split(),
        "sources": retrieval.get("sources", []),
        "fallback_reason": retrieval.get("fallback_reason"),
    }
    enhanced = _merge_rule_template(enhanced, retrieval, quality_control, lesion_analysis)
    llm_result = generate_report_assist_with_llm(
        model_results={"quality_control": quality_control, "lesion_analysis": lesion_analysis, "case_context": case_context},
        rag_context={"snippets": retrieval.get("snippets", []), "sources": retrieval.get("sources", [])},
        safety_constraints={"must_include": [REVIEW_HINT], "forbidden_terms": FORBIDDEN_TERMS},
        output_schema={
            "summary": "string",
            "quality_control_text": "string",
            "lesion_text": "string",
            "structured_findings": "object",
            "suggested_report_sections": {"findings": ["string"], "impression": ["string"], "limitations": ["string"]},
            "recommended_actions": [{"code": "string", "text": "string"}],
            "warnings": ["string"],
        },
    )
    if llm_result.get("status") == "success" and isinstance(llm_result.get("content"), dict):
        llm_content = dict(llm_result["content"])
        llm_content.setdefault("structured_findings", enhanced.get("structured_findings"))
        enhanced.update(llm_content)
    enhanced["rag_enhanced"] = bool(retrieval.get("sources"))
    enhanced["rag_context"] = rag_context
    enhanced["llm_context"] = {
        "enabled": llm_result.get("status") != "disabled",
        "provider": llm_result.get("provider"),
        "model": llm_result.get("model"),
        "status": llm_result.get("status"),
        "prompt_version": "report_assist_v1",
        "safety_rewrites": llm_result.get("safety_rewrites") or [],
        "fallback_reason": llm_result.get("error_message"),
    }
    enhanced, issues = validate_report_safety(enhanced)
    if issues:
        raise ReportEnhancementError(f"report assistance failed safety validation: {'; '.join(issues)}")
    return enhanced
