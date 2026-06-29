"""Safety validation for report and clinical assistance text."""

from __future__ import annotations

from typing import Any


FORBIDDEN_TERMS = [
    "确诊",
    "排除",
    "无需复核",
    "无需医生审核",
    "自动完成诊断",
    "最终诊断为",
]
REVIEW_HINT = "AI 结果仅供辅助参考，最终结论需医生审核。"


def _walk_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_walk_text(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(_walk_text(item))
        return result
    return []


def _report_visible_texts(report_assist: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in ("summary", "quality_control_text", "lesion_text"):
        texts.extend(_walk_text(report_assist.get(key)))
    texts.extend(_walk_text(report_assist.get("suggested_report_sections")))
    texts.extend(_walk_text(report_assist.get("recommended_actions")))
    texts.extend(_walk_text(report_assist.get("warnings")))
    return texts


def validate_report_safety(report_assist: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    joined = "\n".join(_report_visible_texts(report_assist))
    for term in FORBIDDEN_TERMS:
        if term in joined:
            issues.append(f"forbidden_term:{term}")

    limitations = report_assist.setdefault("suggested_report_sections", {}).setdefault("limitations", [])
    if REVIEW_HINT not in limitations:
        limitations.append(REVIEW_HINT)

    warnings = report_assist.setdefault("warnings", [])
    if REVIEW_HINT not in warnings:
        warnings.append(REVIEW_HINT)

    report_assist["requires_doctor_review"] = True
    report_assist["prohibited_claims"] = FORBIDDEN_TERMS
    return report_assist, issues
