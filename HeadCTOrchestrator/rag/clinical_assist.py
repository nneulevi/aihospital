"""RAG + LLM clinical assistance for upstream HIS modules."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

import httpx

from .config import (
    ALI_BAILIAN_API_KEY,
    ALI_BAILIAN_BASE_URL,
    ALI_BAILIAN_MODEL,
    ALI_BAILIAN_TIMEOUT_SECONDS,
    CACHE_LLM_RESPONSE_TTL_SECONDS,
    LLM_ENABLED,
    LLM_PROVIDER,
    RAG_ENABLED,
)
from .retriever import retrieve_context
from .safety_rules import FORBIDDEN_TERMS, REVIEW_HINT

try:
    from ..conversation.memory_service import build_memory_context, get_conversation_store, persist_conversation_turn
except ImportError:  # pragma: no cover - direct script fallback.
    from conversation.memory_service import build_memory_context, get_conversation_store, persist_conversation_turn  # type: ignore

try:
    from ..cache.cache_keys import llm_response_key
    from ..cache.cache_service import clone_json, get_json, set_json
except ImportError:  # pragma: no cover - direct script fallback.
    from cache.cache_keys import llm_response_key  # type: ignore
    from cache.cache_service import clone_json, get_json, set_json  # type: ignore


class ClinicalAssistError(RuntimeError):
    pass


CLINICAL_SYSTEM_PROMPT = (
    "你是医院主平台中的 AI 辅助问诊与辅助诊断模块。"
    "你必须只输出合法 JSON，不输出 Markdown。"
    "你不能给出最终诊断，不能宣称已经确诊、无需医生审核或自动完成诊断。"
    "所有结论必须表述为 AI 辅助参考，并明确最终结论需医生结合病史、体格检查、检验检查和影像资料审核。"
)

HIGH_RISK_FORBIDDEN_PATTERNS = [
    "确诊",
    "无需复核",
    "无需医生审核",
    "自动完成诊断",
    "最终诊断为",
]

SAFETY_REWRITES = [
    ("不能排除", "仍需结合临床与检查结果评估"),
    ("无法排除", "仍需结合临床与检查结果评估"),
    ("确诊为", "AI 辅助提示倾向"),
    ("确诊", "AI 辅助提示"),
    ("排除", "未见明确提示"),
    ("无需医生审核", "需医生审核"),
    ("无需复核", "需医生复核"),
    ("自动完成诊断", "生成辅助诊断建议"),
    ("最终诊断为", "AI 辅助提示"),
]


def _json_from_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ClinicalAssistError("LLM response must be a JSON object")
    return parsed


def _validate_safety(value: Any) -> list[str]:
    texts: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, dict):
            for child in item.values():
                walk(child)

    walk(value)
    merged = "\n".join(texts)
    return [term for term in HIGH_RISK_FORBIDDEN_PATTERNS if term and term in merged]


def _sanitize_safety_text(value: Any) -> Any:
    if isinstance(value, str):
        updated = value
        for source, replacement in SAFETY_REWRITES:
            updated = updated.replace(source, replacement)
        return updated
    if isinstance(value, list):
        return [_sanitize_safety_text(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_safety_text(item) for key, item in value.items()}
    return value


def _call_bailian(messages: list[dict[str, str]]) -> dict[str, Any]:
    if not LLM_ENABLED or LLM_PROVIDER != "aliyun_bailian":
        raise ClinicalAssistError("LLM is not enabled or LLM_PROVIDER is not aliyun_bailian")
    if not ALI_BAILIAN_API_KEY:
        raise ClinicalAssistError("ALI_BAILIAN_API_KEY is not configured")
    with httpx.Client(timeout=ALI_BAILIAN_TIMEOUT_SECONDS) as client:
        response = client.post(
            f"{ALI_BAILIAN_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {ALI_BAILIAN_API_KEY}"},
            json={"model": ALI_BAILIAN_MODEL, "messages": messages, "temperature": 0.2},
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    parsed = _json_from_text(content)
    hits = _validate_safety(parsed)
    if hits:
        parsed = _sanitize_safety_text(parsed)
        hits = _validate_safety(parsed)
    if hits:
        raise ClinicalAssistError("LLM output failed safety validation: " + ",".join(hits))
    return parsed


def _call_bailian_cached(
    *,
    cache_kind: str,
    prompt_payload: dict[str, Any],
    messages: list[dict[str, str]],
) -> tuple[dict[str, Any], bool, str]:
    cache_payload = {
        "provider": LLM_PROVIDER,
        "model": ALI_BAILIAN_MODEL,
        "kind": cache_kind,
        "prompt_payload": prompt_payload,
    }
    cache_key = llm_response_key(cache_kind, cache_payload)
    cache_hit, cached = get_json(cache_key)
    if cache_hit and isinstance(cached, dict):
        parsed = clone_json(cached)
        if isinstance(parsed, dict):
            parsed = _sanitize_safety_text(parsed)
            hits = _validate_safety(parsed)
            if hits:
                raise ClinicalAssistError("Cached LLM output failed safety validation: " + ",".join(hits))
            return parsed, True, "redis"

    parsed = _call_bailian(messages)
    stored = set_json(cache_key, parsed, CACHE_LLM_RESPONSE_TTL_SECONDS)
    return parsed, False, "redis" if stored else "disabled"


def _retrieve(query_text: str) -> dict[str, Any]:
    if not RAG_ENABLED:
        raise ClinicalAssistError("RAG is not enabled")
    return retrieve_context(query_text, filter_tags=None)


def _memory_for_prompt(payload: dict[str, Any], scene: str, current_user_message: str) -> tuple[object | None, dict[str, Any], dict[str, Any]]:
    memory_payload = dict(payload)
    memory_payload["scene"] = scene
    store = get_conversation_store()
    if memory_payload.get("conversation_id") and memory_payload.get("memory_enabled") is not False and store is None:
        raise ClinicalAssistError("conversation memory store is not configured")
    context = build_memory_context(store, memory_payload, current_user_message)
    return store, memory_payload, context


def _base_payload(kind: str, query_text: str, retrieval: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": uuid.uuid4().hex,
        "kind": kind,
        "query_text": query_text,
        "rag_context": {
            "enabled": True,
            "status": retrieval.get("status"),
            "retrieval_confidence": retrieval.get("retrieval_confidence", 0.0),
            "sources": retrieval.get("sources", []),
            "fallback_reason": retrieval.get("fallback_reason"),
            "recall_count": retrieval.get("recall_count"),
            "cache_hit": retrieval.get("cache_hit", False),
            "cache_backend": retrieval.get("cache_backend"),
        },
        "llm_context": {
            "enabled": True,
            "provider": "aliyun_bailian",
            "model": ALI_BAILIAN_MODEL,
            "status": "success",
            "prompt_version": "clinical_assist_v1",
        },
        "requires_doctor_review": True,
        "safety_notice": REVIEW_HINT,
    }


def generate_consultation_assist(payload: dict[str, Any]) -> dict[str, Any]:
    symptoms = str(payload.get("symptoms") or "").strip()
    patient_id = payload.get("patient_id")
    if not symptoms:
        raise ClinicalAssistError("symptoms is required")
    query_text = f"AI triage consultation symptoms: {symptoms}"
    retrieval = _retrieve(query_text)
    memory_store, memory_payload, memory_context = _memory_for_prompt(payload, "consultation", symptoms)
    prompt_payload = {
        "task": "triage_consultation",
        "patient_id": patient_id,
        "symptoms": symptoms,
        "conversation_memory": memory_context,
        "rag_snippets": retrieval.get("snippets", []),
        "safety_constraints": {
            "must_include": REVIEW_HINT,
            "forbidden_terms": FORBIDDEN_TERMS,
        },
        "output_schema": {
            "recommendations": [
                {"dept_id": "integer_or_null", "dept_name": "string", "confidence": "number_0_to_1", "reason": "string"}
            ],
            "diagnosis_hint": "string",
        },
    }
    messages = [
        {"role": "system", "content": CLINICAL_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
    ]
    content, llm_cache_hit, llm_cache_backend = _call_bailian_cached(
        cache_kind="clinical_consultation",
        prompt_payload=prompt_payload,
        messages=messages,
    )
    result = _base_payload("consultation", query_text, retrieval)
    result["llm_context"]["cache_hit"] = llm_cache_hit
    result["llm_context"]["cache_backend"] = llm_cache_backend
    result["recommendations"] = content.get("recommendations") or []
    result["diagnosis_hint"] = content.get("diagnosis_hint") or REVIEW_HINT
    result["memory_context"] = memory_context
    persist_conversation_turn(
        memory_store,
        memory_payload,
        user_message=symptoms,
        assistant_payload={
            "recommendations": result["recommendations"],
            "diagnosis_hint": result["diagnosis_hint"],
        },
    )
    return result


def generate_diagnosis_assist(payload: dict[str, Any]) -> dict[str, Any]:
    symptoms = str(payload.get("symptoms") or "").strip()
    history = str(payload.get("history") or "").strip()
    physique = str(payload.get("physique") or "").strip()
    medical_record_id = payload.get("medical_record_id")
    query_text = " ".join(
        item
        for item in [
            "AI diagnosis suggestion",
            f"symptoms: {symptoms}",
            f"history: {history}",
            f"physical exam: {physique}",
        ]
        if item
    )
    if not query_text.strip():
        raise ClinicalAssistError("at least one clinical text field is required")
    retrieval = _retrieve(query_text)
    memory_store, memory_payload, memory_context = _memory_for_prompt(payload, "diagnosis", query_text)
    prompt_payload = {
        "task": "diagnosis_suggestion",
        "medical_record_id": medical_record_id,
        "symptoms": symptoms,
        "history": history,
        "physique": physique,
        "conversation_memory": memory_context,
        "rag_snippets": retrieval.get("snippets", []),
        "safety_constraints": {
            "must_include": REVIEW_HINT,
            "forbidden_terms": FORBIDDEN_TERMS,
        },
        "output_schema": {
            "suggestions": [
                {
                    "disease_id": "integer_or_null",
                    "disease_code": "string",
                    "disease_name": "string",
                    "confidence": "number_0_to_1",
                    "evidence": "string",
                }
            ],
        },
    }
    messages = [
        {"role": "system", "content": CLINICAL_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
    ]
    content, llm_cache_hit, llm_cache_backend = _call_bailian_cached(
        cache_kind="clinical_diagnosis",
        prompt_payload=prompt_payload,
        messages=messages,
    )
    result = _base_payload("diagnosis", query_text, retrieval)
    result["llm_context"]["cache_hit"] = llm_cache_hit
    result["llm_context"]["cache_backend"] = llm_cache_backend
    result["suggestions"] = content.get("suggestions") or []
    result["memory_context"] = memory_context
    persist_conversation_turn(
        memory_store,
        memory_payload,
        user_message=query_text,
        assistant_payload={"suggestions": result["suggestions"]},
    )
    return result
