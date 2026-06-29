from __future__ import annotations

from HeadCTReportService.services.report_service import draft_sections


def test_draft_sections_expand_structured_ai_findings() -> None:
    result = {
        "report_assist": {
            "summary": "AI辅助分析提示疑似颅内出血。",
            "quality_control_text": "存在中度金属伪影。",
            "lesion_text": "AI提示疑似颅内出血。",
            "structured_findings": {
                "quality": {
                    "artifact_detected": True,
                    "artifact_severity": "moderate",
                    "affected_slices": [6, 7, 8],
                    "artifact_ratio": 0.18,
                    "interpretation": "受影响层面局部结构显示受限。",
                },
                "lesions": [
                    {
                        "lesion_type": "intracranial_hemorrhage",
                        "detected": True,
                        "confidence": 0.82,
                        "location": "右侧基底节区",
                        "slice_range": [6, 8],
                        "evidence": "局部高密度影，边界欠清。",
                    }
                ],
                "review_focus": ["重点复核第6-8层右侧基底节区及伪影邻近区域。"],
            },
            "suggested_report_sections": {
                "findings": ["AI提示疑似颅内出血。"],
                "impression": ["AI辅助分析提示右侧基底节区疑似颅内出血相关征象。"],
                "limitations": ["AI结果仅供辅助参考，最终结论需医生审核。"],
            },
            "recommended_actions": [{"code": "review_original_ct", "text": "复核原始CT。"}],
            "warnings": [],
        }
    }
    sections = draft_sections(result)
    assert "影像质量评估" in sections["findings"]
    assert "中度金属伪影" in sections["findings"]
    assert "右侧基底节区" in sections["findings"]
    assert "第6-8层" in sections["findings"]
    assert "置信度0.82" in sections["findings"]
    assert "诊断辅助意见" in sections["impression"]
    assert "医生审核" in sections["recommendations"]
