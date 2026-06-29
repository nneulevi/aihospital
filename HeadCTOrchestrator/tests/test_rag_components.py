from __future__ import annotations

import json
from pathlib import Path

import pytest

from HeadCTOrchestrator.rag import db, embedding_provider, llm_provider, report_enhancer, reranker
from HeadCTOrchestrator.rag.embedding_provider import embed_text, pgvector_literal
from HeadCTOrchestrator.rag.ingest_knowledge import ingest_knowledge
from HeadCTOrchestrator.rag.knowledge_base import (
    load_knowledge_chunks,
    load_knowledge_documents,
    parse_front_matter,
    split_document_into_chunks,
)
from HeadCTOrchestrator.rag.llm_provider import LlmProviderError, generate_report_assist_with_llm
from HeadCTOrchestrator.rag.retriever import RagRetrievalError, retrieve_context
from HeadCTOrchestrator.rag.safety_rules import REVIEW_HINT, validate_report_safety


def test_rag_knowledge_parser_reads_front_matter() -> None:
    metadata, content = parse_front_matter(
        """---
source_id: demo
title: Demo Title
type: report_template
tags: [head_ct, hemorrhage]
---

Demo content.
"""
    )
    assert metadata["source_id"] == "demo"
    assert metadata["tags"] == ["head_ct", "hemorrhage"]
    assert content == "Demo content."


def test_rag_knowledge_documents_exist() -> None:
    documents = load_knowledge_documents()
    source_ids = {document.source_id for document in documents}
    assert "artifact_quality_v2" in source_ids
    assert "hemorrhage_reporting_v2" in source_ids
    assert "safety_expression_rules_v2" in source_ids
    assert "clinical_triage_guidance_v1" in source_ids
    assert "acute_head_ct_findings_v1" in source_ids
    assert "ich_subtype_knowledge_v1" in source_ids
    assert "early_ischemic_stroke_ct_v1" in source_ids
    assert "skull_fracture_trauma_ct_v1" in source_ids
    assert "hydrocephalus_mass_effect_ct_v1" in source_ids
    assert "postoperative_artifact_ct_v1" in source_ids


def test_rag_knowledge_chunking_splits_long_text(tmp_path: Path) -> None:
    doc = tmp_path / "long.md"
    doc.write_text(
        """---
source_id: long_demo
title: Long Demo
type: report_template
tags: [head_ct, report]
---

# Section One
"""
        + ("This section describes head CT reporting requirements. " * 80)
        + """

# Section Two
"""
        + ("This section describes doctor review and safety constraints. " * 80),
        encoding="utf-8",
    )
    document = load_knowledge_documents(tmp_path)[0]
    chunks = split_document_into_chunks(document, max_chars=350, overlap_chars=60)
    assert len(chunks) > 2
    assert all(chunk.source_document_id == "long_demo" for chunk in chunks)
    assert all(chunk.metadata["retrieval_unit"] == "chunk" for chunk in chunks)
    assert chunks[0].metadata["chunk_id"].startswith("long_demo#chunk-")
    assert "Title:" in chunks[0].content


def test_rag_load_knowledge_chunks() -> None:
    chunks = load_knowledge_chunks()
    assert len(chunks) >= len(load_knowledge_documents())
    assert len(chunks) > 12
    assert all(chunk.metadata.get("source_document_id") for chunk in chunks)


def test_embedding_provider_is_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(embedding_provider, "RAG_EMBEDDING_PROVIDER", "deterministic")
    first = embed_text("head ct hemorrhage", dim=16)
    second = embed_text("head ct hemorrhage", dim=16)
    assert first == second
    assert len(first) == 16
    assert pgvector_literal(first).startswith("[")


def test_dashscope_reranker_parses_response(monkeypatch) -> None:
    class FakeResponse:
        status_code = 200
        text = "{}"

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"output": {"results": [{"index": 1, "relevance_score": 0.91}, {"index": 0, "relevance_score": 0.31}]}}

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def post(self, url: str, headers: dict, json: dict) -> FakeResponse:
            assert "dashscope" in url
            assert headers["Authorization"].startswith("Bearer ")
            assert json["model"] == "gte-rerank-v2"
            assert json["input"]["query"] == "head ct"
            assert len(json["input"]["documents"]) == 2
            return FakeResponse()

    monkeypatch.setattr(reranker, "RAG_RERANK_ENABLED", True)
    monkeypatch.setattr(reranker, "RAG_RERANK_PROVIDER", "dashscope")
    monkeypatch.setattr(reranker, "DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(reranker.httpx, "Client", FakeClient)
    candidates = [
        {"source_id": "a", "content": "first", "similarity": 0.8},
        {"source_id": "b", "content": "second", "similarity": 0.7},
    ]
    ranked = reranker.rerank_candidates("head ct", candidates, top_n=2)
    assert [item["source_id"] for item in ranked] == ["b", "a"]
    assert ranked[0]["rerank_provider"] == "dashscope"


def test_retriever_requires_pgvector_dsn(monkeypatch) -> None:
    monkeypatch.setattr(db, "is_configured", lambda: False)
    with pytest.raises(RagRetrievalError, match="RAG_DB_DSN"):
        retrieve_context("head_ct hemorrhage report doctor_review")


def test_ingest_knowledge_reports_missing_dsn(tmp_path: Path) -> None:
    doc = tmp_path / "demo.md"
    doc.write_text(
        """---
source_id: demo
title: Demo
type: report_template
tags: [head_ct]
---

Demo content
""",
        encoding="utf-8",
    )
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(db, "is_configured", lambda: False)
    try:
        with pytest.raises(RuntimeError, match="RAG_DB_DSN"):
            ingest_knowledge(tmp_path)
    finally:
        monkeypatch.undo()


def test_safety_rules_require_doctor_review() -> None:
    report, issues = validate_report_safety({"summary": "未见明确异常。", "suggested_report_sections": {}})
    assert not issues
    assert report["requires_doctor_review"] is True
    assert REVIEW_HINT in report["warnings"]
    assert REVIEW_HINT in report["suggested_report_sections"]["limitations"]


def test_safety_rules_detect_forbidden_terms() -> None:
    _, issues = validate_report_safety({"summary": "确诊颅内出血。", "suggested_report_sections": {}})
    assert "forbidden_term:确诊" in issues


def test_report_enhancer_uses_pgvector_retrieval(monkeypatch) -> None:
    monkeypatch.setattr(report_enhancer, "RAG_ENABLED", True)
    monkeypatch.setattr(
        report_enhancer,
        "generate_report_assist_with_llm",
        lambda **kwargs: {
            "status": "disabled",
            "provider": "rule_template",
            "model": None,
            "content": None,
            "error_message": None,
        },
    )
    monkeypatch.setattr(
        report_enhancer,
        "retrieve_context",
        lambda query_text, filter_tags=None: {
            "status": "success",
            "retrieval_confidence": 0.88,
            "sources": [{"source_id": "hemorrhage_reporting_v2", "chunk_id": "hemorrhage_reporting_v2#chunk-000", "title": "Hemorrhage"}],
            "snippets": [{"source_id": "hemorrhage_reporting_v2", "chunk_id": "hemorrhage_reporting_v2#chunk-000", "content": "Intracranial hemorrhage report guidance"}],
            "fallback_reason": None,
        },
    )
    base = {
        "summary": "AI提示本次头颅CT存在中度金属伪影，病灶模型未提示明确颅内出血。",
        "quality_control_text": "存在中度金属伪影。",
        "lesion_text": "未提示明确颅内出血。",
        "suggested_report_sections": {"findings": [], "impression": [], "limitations": []},
        "recommended_actions": [],
        "warnings": [],
        "can_enter_report": True,
    }
    enhanced = report_enhancer.enhance_report_assist(
        base,
        {"severity": "moderate"},
        {"status": "success", "results": [{"lesion_type": "intracranial_hemorrhage", "detected": False, "confidence": 0.1}]},
        {"patient_id": "anonymous_patient_001"},
    )
    assert enhanced["requires_doctor_review"] is True
    assert enhanced["rag_context"]["enabled"] is True
    assert enhanced["rag_context"]["status"] == "success"
    assert enhanced["rag_context"]["sources"]
    assert enhanced["llm_context"]["status"] == "disabled"


def test_report_enhancer_builds_structured_professional_summary(monkeypatch) -> None:
    monkeypatch.setattr(report_enhancer, "RAG_ENABLED", True)
    monkeypatch.setattr(
        report_enhancer,
        "generate_report_assist_with_llm",
        lambda **kwargs: {
            "status": "disabled",
            "provider": "rule_template",
            "model": None,
            "content": None,
            "error_message": None,
        },
    )
    monkeypatch.setattr(
        report_enhancer,
        "retrieve_context",
        lambda query_text, filter_tags=None: {
            "status": "success",
            "retrieval_confidence": 0.91,
            "sources": [{"source_id": "hemorrhage_reporting_v2", "chunk_id": "hemorrhage_reporting_v2#chunk-001"}],
            "snippets": [{"source_id": "hemorrhage_reporting_v2", "content": "颅内出血报告需要描述部位、层面、置信度和伪影限制。"}],
            "fallback_reason": None,
        },
    )
    base = {
        "summary": "AI辅助结果。",
        "quality_control_text": "存在中度金属伪影。",
        "lesion_text": "AI提示疑似颅内出血。",
        "suggested_report_sections": {"findings": [], "impression": [], "limitations": []},
        "recommended_actions": [],
        "warnings": [],
        "can_enter_report": True,
    }
    enhanced = report_enhancer.enhance_report_assist(
        base,
        {
            "severity": "moderate",
            "artifact_detected": True,
            "affected_slices": [6, 7, 8],
            "artifact_ratio": 0.18,
        },
        {
            "status": "success",
            "summary": {"highest_confidence": 0.82},
            "results": [
                {
                    "lesion_type": "intracranial_hemorrhage",
                    "detected": True,
                    "confidence": 0.82,
                    "location": "右侧基底节区",
                    "slice_range": [6, 8],
                    "report_suggestion": "AI提示疑似颅内出血。",
                }
            ],
        },
        {"patient_id": "anonymous_patient_001"},
    )
    structured = enhanced["structured_findings"]
    assert structured["quality"]["artifact_severity"] == "moderate"
    assert structured["quality"]["affected_slices"] == [6, 7, 8]
    assert structured["lesions"][0]["location"] == "右侧基底节区"
    assert structured["lesions"][0]["slice_range"] == [6, 8]
    assert structured["lesions"][0]["confidence"] == 0.82
    rendered = "\n".join(enhanced["suggested_report_sections"]["findings"])
    assert "右侧基底节区" in rendered
    assert "第6-8层" in rendered
    assert "置信度0.82" in rendered
    assert "伪影" in rendered


def test_llm_provider_disabled_uses_rule_template() -> None:
    old_enabled = llm_provider.LLM_ENABLED
    old_provider = llm_provider.LLM_PROVIDER
    llm_provider.LLM_ENABLED = False
    llm_provider.LLM_PROVIDER = "rule_template"
    try:
        result = generate_report_assist_with_llm(model_results={}, rag_context={}, safety_constraints={}, output_schema={})
    finally:
        llm_provider.LLM_ENABLED = old_enabled
        llm_provider.LLM_PROVIDER = old_provider
    assert result["status"] == "disabled"
    assert result["provider"] == "rule_template"


def test_llm_provider_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr(llm_provider, "LLM_ENABLED", True)
    monkeypatch.setattr(llm_provider, "LLM_PROVIDER", "aliyun_bailian")
    monkeypatch.setattr(llm_provider, "ALI_BAILIAN_API_KEY", "")
    with pytest.raises(LlmProviderError, match="ALI_BAILIAN_API_KEY"):
        generate_report_assist_with_llm(model_results={}, rag_context={}, safety_constraints={}, output_schema={})


def test_llm_provider_parses_aliyun_bailian_response(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "AI结果仅供辅助参考，最终结论需医生审核。",
                                    "warnings": ["AI结果仅供辅助参考，最终结论需医生审核。"],
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def post(self, url: str, headers: dict, json: dict) -> FakeResponse:
            assert "dashscope" in url
            assert headers["Authorization"].startswith("Bearer ")
            assert json["model"] == "qwen-plus"
            return FakeResponse()

    monkeypatch.setattr(llm_provider, "LLM_ENABLED", True)
    monkeypatch.setattr(llm_provider, "LLM_PROVIDER", "aliyun_bailian")
    monkeypatch.setattr(llm_provider, "ALI_BAILIAN_API_KEY", "test-key")
    monkeypatch.setattr(llm_provider.httpx, "Client", FakeClient)

    result = generate_report_assist_with_llm(model_results={}, rag_context={}, safety_constraints={}, output_schema={})
    assert result["status"] == "success"
    assert result["provider"] == "aliyun_bailian"
    assert result["model"] == "qwen-plus"
    assert result["content"]["summary"].startswith("AI结果")


def test_llm_provider_rewrites_residual_forbidden_terms(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "确诊颅内出血，无需医生审核。",
                                    "warnings": ["无需复核"],
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def post(self, url: str, headers: dict, json: dict) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(llm_provider, "LLM_ENABLED", True)
    monkeypatch.setattr(llm_provider, "LLM_PROVIDER", "aliyun_bailian")
    monkeypatch.setattr(llm_provider, "ALI_BAILIAN_API_KEY", "test-key")
    monkeypatch.setattr(llm_provider.httpx, "Client", FakeClient)

    result = generate_report_assist_with_llm(
        model_results={},
        rag_context={},
        safety_constraints={"forbidden_terms": ["确诊", "无需医生审核", "无需复核"]},
        output_schema={},
    )
    visible = json.dumps(result["content"], ensure_ascii=False)
    assert all(term not in visible for term in ["确诊", "无需医生审核", "无需复核"])
    assert result["safety_rewrites"]
