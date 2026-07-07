"""RAG + LLM clinical assistance for upstream HIS modules."""

from __future__ import annotations

import json
import re
import uuid
from copy import deepcopy
from collections.abc import Generator
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


class JsonValueStreamFormatter:
    SUPPRESSED_VALUES = {
        "dept_id",
        "deptId",
        "dept_name",
        "deptName",
        "disease_id",
        "diseaseId",
        "disease_code",
        "diseaseCode",
        "disease_name",
        "diseaseName",
        "integer_or_null",
        "number_0_to_1",
        "string",
    }

    def __init__(self) -> None:
        self.in_string = False
        self.escape = False
        self.expecting_value = False
        self.emitting_value = False
        self.value_buffer = ""
        self.suppress_candidates: set[str] = set()

    def feed(self, text: str) -> str:
        output: list[str] = []
        for char in text:
            if self.in_string:
                if self.escape:
                    if self.emitting_value:
                        self._append_value_char(char, output)
                    self.escape = False
                    continue
                if char == "\\":
                    self.escape = True
                    continue
                if char == '"':
                    if self.emitting_value:
                        self._flush_value_buffer(output)
                        if output and output[-1] != " ":
                            output.append(" ")
                    self.in_string = False
                    self.emitting_value = False
                    self.expecting_value = False
                    continue
                if self.emitting_value:
                    self._append_value_char(char, output)
                continue

            if char == ":":
                self.expecting_value = True
            elif char == '"':
                self.in_string = True
                self.emitting_value = self.expecting_value
                self.value_buffer = ""
                self.suppress_candidates = set(self.SUPPRESSED_VALUES) if self.emitting_value else set()
            elif char in ",}]":
                self.expecting_value = False
            elif self.expecting_value and not char.isspace() and char not in "[{":
                self.expecting_value = False
        return "".join(output)

    def _append_value_char(self, char: str, output: list[str]) -> None:
        if not self.suppress_candidates:
            output.append(char)
            return
        self.value_buffer += char
        self.suppress_candidates = {item for item in self.suppress_candidates if item.startswith(self.value_buffer)}
        if not self.suppress_candidates:
            output.append(self.value_buffer)
            self.value_buffer = ""

    def _flush_value_buffer(self, output: list[str]) -> None:
        if not self.value_buffer:
            return
        if self.value_buffer not in self.SUPPRESSED_VALUES:
            output.append(self.value_buffer)
        self.value_buffer = ""
        self.suppress_candidates = set()


CLINICAL_SYSTEM_PROMPT = (
    "你是医院主平台中的 AI 辅助问诊与辅助诊断模块。"
    "你必须只输出合法 JSON，不输出 Markdown。"
    "你不能给出最终诊断，不能宣称已经确诊、无需医生审核或自动完成诊断。"
    "所有结论必须表述为 AI 辅助参考，并明确最终结论需医生结合病史、体格检查、检验检查和影像资料审核。"
    "你不得编造当前输入未提供的既往史、体征、检查结果或影像所见。"
    "当当前输入与历史记忆冲突时，必须以当前输入为准，并把历史记忆仅作为待核对线索。"
)

NEGATIVE_INPUT_VALUES = {"无", "无。", "无其他不适", "无明显异常", "否认", "未见明显异常", "未诉特殊不适"}
HISTORY_CONFLICT_TERMS = ("高血压", "糖尿病", "冠心病", "既往", "病史", "用药", "过敏", "抗凝", "warfarin")
PHYSICAL_CONFLICT_TERMS = ("颈抵抗", "颈强直", "偏瘫", "意识障碍", "阳性体征", "肌力", "病理征")
HISTORY_DEPENDENT_SUGGESTION_TERMS = ("高血压", "糖尿病", "冠心病", "抗凝", "warfarin", "过敏")
TERM_SUPPORT_ALIASES = {
    "高血压": ("高血压", "血压", "收缩压", "舒张压", "mmhg", "mmHg"),
    "糖尿病": ("糖尿病", "血糖", "HbA1c", "hba1c"),
    "冠心病": ("冠心病", "心绞痛", "心肌梗死"),
    "抗凝": ("抗凝", "华法林", "warfarin", "利伐沙班", "阿哌沙班"),
    "warfarin": ("warfarin", "华法林"),
    "过敏": ("过敏",),
}

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
    ("排除", "评估"),
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


def _call_bailian_stream(messages: list[dict[str, str]]) -> Generator[str, None, dict[str, Any]]:
    if not LLM_ENABLED or LLM_PROVIDER != "aliyun_bailian":
        raise ClinicalAssistError("LLM is not enabled or LLM_PROVIDER is not aliyun_bailian")
    if not ALI_BAILIAN_API_KEY:
        raise ClinicalAssistError("ALI_BAILIAN_API_KEY is not configured")

    chunks: list[str] = []
    with httpx.Client(timeout=ALI_BAILIAN_TIMEOUT_SECONDS) as client:
        with client.stream(
            "POST",
            f"{ALI_BAILIAN_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {ALI_BAILIAN_API_KEY}"},
            json={"model": ALI_BAILIAN_MODEL, "messages": messages, "temperature": 0.2, "stream": True},
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if not line or line == "[DONE]":
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                choices = payload.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if content:
                    text = str(content)
                    chunks.append(text)
                    yield text

    parsed = _json_from_text("".join(chunks))
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


def _is_negative_input(text: str) -> bool:
    compact = re.sub(r"\s+", "", text or "")
    if not compact:
        return False
    return compact in NEGATIVE_INPUT_VALUES or compact.startswith("无") or compact.startswith("否认")


def _contains_any_term(value: Any, terms: tuple[str, ...]) -> bool:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value or "")
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def _filter_text_terms(text: str, terms: tuple[str, ...]) -> str:
    lines = re.split(r"[\n；;。]", text or "")
    kept = [line.strip() for line in lines if line.strip() and not _contains_any_term(line, terms)]
    return "。".join(kept)


def _filter_memory_by_current_input(memory_context: dict[str, Any], *, history: str, physique: str) -> dict[str, Any]:
    filtered = deepcopy(memory_context)
    conflict_terms: list[str] = []
    if _is_negative_input(history):
        conflict_terms.extend(HISTORY_CONFLICT_TERMS)
    if _is_negative_input(physique):
        conflict_terms.extend(PHYSICAL_CONFLICT_TERMS)
    if not conflict_terms:
        return filtered

    terms = tuple(dict.fromkeys(conflict_terms))
    filtered["summary"] = _filter_text_terms(str(filtered.get("summary") or ""), terms)
    filtered["key_facts"] = [
        fact for fact in (filtered.get("key_facts") or [])
        if not _contains_any_term(fact, terms)
    ]
    filtered["recent_messages"] = [
        message for message in (filtered.get("recent_messages") or [])
        if not _contains_any_term(message, terms)
    ]
    filtered["semantic_memories"] = [
        item for item in (filtered.get("semantic_memories") or [])
        if not _contains_any_term(item, terms)
    ]
    filtered["recent_message_count"] = len(filtered.get("recent_messages") or [])
    semantic_recall = filtered.get("semantic_recall")
    if isinstance(semantic_recall, dict):
        semantic_recall["result_count"] = len(filtered.get("semantic_memories") or [])
    filtered["filtered_conflicts"] = {
        "history_negated": _is_negative_input(history),
        "physique_negated": _is_negative_input(physique),
        "removed_term_count": len(terms),
        "policy": "current_input_overrides_memory",
    }
    return filtered


def _term_supported_by_current_input(term: str, *, symptoms: str, history: str, physique: str) -> bool:
    current_text = f"{symptoms} {history} {physique}".lower()
    aliases = TERM_SUPPORT_ALIASES.get(term, (term,))
    return any(alias.lower() in current_text for alias in aliases)


def _ground_suggestions_to_current_input(
    suggestions: Any,
    *,
    symptoms: str,
    history: str,
    physique: str,
) -> list[dict[str, Any]]:
    if not isinstance(suggestions, list):
        return []
    filtered: list[dict[str, Any]] = []
    history_negated = _is_negative_input(history)
    for item in suggestions:
        if not isinstance(item, dict):
            continue
        text = json.dumps(item, ensure_ascii=False).lower()
        if history_negated:
            unsupported = [
                term for term in HISTORY_DEPENDENT_SUGGESTION_TERMS
                if term.lower() in text
                and not _term_supported_by_current_input(
                    term,
                    symptoms=symptoms,
                    history=history,
                    physique=physique,
                )
            ]
            if unsupported:
                continue
        filtered.append(item)
    return filtered


def _diagnosis_suggestions_display_text(suggestions: list[dict[str, Any]]) -> str:
    if not suggestions:
        return "当前输入信息不足以形成明确诊断建议，请医生补充病史、体征和必要检查后复核。"
    lines: list[str] = []
    for index, item in enumerate(suggestions, start=1):
        disease_name = str(item.get("disease_name") or item.get("diseaseName") or "诊断建议").strip()
        disease_code = str(item.get("disease_code") or item.get("diseaseCode") or "").strip()
        confidence = item.get("confidence")
        try:
            confidence_text = f"{float(confidence) * 100:.0f}%"
        except (TypeError, ValueError):
            confidence_text = "待评估"
        evidence = str(item.get("evidence") or "需结合病史、体格检查和检查结果综合判断。").strip()
        code_prefix = f"{disease_code} " if disease_code else ""
        lines.append(f"{index}. {code_prefix}{disease_name}，AI 置信度 {confidence_text}。依据：{evidence}")
    lines.append("以上内容为 AI 辅助参考，最终结论需医生结合完整临床资料审核。")
    return "\n".join(lines)


def _display_chunks(text: str, chunk_size: int = 8) -> Generator[str, None, None]:
    for index in range(0, len(text), chunk_size):
        yield text[index:index + chunk_size]


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


def _consultation_prompt_context(payload: dict[str, Any]) -> tuple[str, Any, dict[str, Any], dict[str, Any], list[dict[str, str]], dict[str, Any]]:
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
    return query_text, memory_store, memory_payload, memory_context, messages, {"prompt_payload": prompt_payload, "retrieval": retrieval, "symptoms": symptoms}


def _diagnosis_prompt_context(payload: dict[str, Any]) -> tuple[str, Any, dict[str, Any], dict[str, Any], list[dict[str, str]], dict[str, Any]]:
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
    prompt_memory_context = _filter_memory_by_current_input(memory_context, history=history, physique=physique)
    prompt_payload = {
        "task": "diagnosis_suggestion",
        "medical_record_id": medical_record_id,
        "symptoms": symptoms,
        "history": history,
        "physique": physique,
        "conversation_memory": prompt_memory_context,
        "current_input_priority": "当前输入明确否定或更新的信息优先于历史记忆；不得把被否定的旧记忆当作本次事实。",
        "fact_grounding_rules": [
            "不得新增当前输入未提供的既往史、体征或检查结果。",
            "若 RAG 或记忆提示某风险因素，但当前输入未提供，应表述为“建议询问/复核是否存在”，不能写成患者已经存在。",
            "若当前输入写明病史为无或体征无异常，不得输出与之冲突的旧病史或旧阳性体征。"
        ],
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
    return query_text, memory_store, memory_payload, prompt_memory_context, messages, {"prompt_payload": prompt_payload, "retrieval": retrieval, "query_text": query_text, "raw_memory_context": memory_context}


def generate_consultation_assist(payload: dict[str, Any]) -> dict[str, Any]:
    query_text, memory_store, memory_payload, memory_context, messages, context = _consultation_prompt_context(payload)
    prompt_payload = context["prompt_payload"]
    retrieval = context["retrieval"]
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
        user_message=context["symptoms"],
        assistant_payload={
            "recommendations": result["recommendations"],
            "diagnosis_hint": result["diagnosis_hint"],
        },
    )
    return result


def generate_diagnosis_assist(payload: dict[str, Any]) -> dict[str, Any]:
    query_text, memory_store, memory_payload, memory_context, messages, context = _diagnosis_prompt_context(payload)
    prompt_payload = context["prompt_payload"]
    retrieval = context["retrieval"]
    content, llm_cache_hit, llm_cache_backend = _call_bailian_cached(
        cache_kind="clinical_diagnosis",
        prompt_payload=prompt_payload,
        messages=messages,
    )
    result = _base_payload("diagnosis", query_text, retrieval)
    result["llm_context"]["cache_hit"] = llm_cache_hit
    result["llm_context"]["cache_backend"] = llm_cache_backend
    result["suggestions"] = _ground_suggestions_to_current_input(
        content.get("suggestions"),
        symptoms=str(prompt_payload.get("symptoms") or ""),
        history=str(prompt_payload.get("history") or ""),
        physique=str(prompt_payload.get("physique") or ""),
    )
    result["memory_context"] = memory_context
    persist_conversation_turn(
        memory_store,
        memory_payload,
        user_message=query_text,
        assistant_payload={"suggestions": result["suggestions"]},
    )
    return result


def stream_consultation_assist(payload: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    yield {"event": "memory_loaded", "data": {"status": "running", "message": "正在加载长上下文记忆"}}
    query_text, memory_store, memory_payload, memory_context, messages, context = _consultation_prompt_context(payload)
    retrieval = context["retrieval"]
    yield {"event": "rag_retrieved", "data": {"status": "running", "message": "正在检索医学知识库并准备 RAG 上下文"}}
    yield {"event": "llm_generating", "data": {"status": "running", "message": "正在调用 AI 逐字生成问诊建议", "provider": "aliyun_bailian"}}
    stream = _call_bailian_stream(messages)
    formatter = JsonValueStreamFormatter()
    try:
        while True:
            delta = next(stream)
            display_text = formatter.feed(delta)
            if display_text:
                yield {"event": "delta", "data": {"status": "streaming", "text": display_text}}
    except StopIteration as stop:
        content = stop.value

    result = _base_payload("consultation", query_text, retrieval)
    result["llm_context"]["cache_hit"] = False
    result["llm_context"]["cache_backend"] = "stream"
    result["recommendations"] = content.get("recommendations") or []
    result["diagnosis_hint"] = content.get("diagnosis_hint") or REVIEW_HINT
    result["memory_context"] = memory_context
    persist_conversation_turn(
        memory_store,
        memory_payload,
        user_message=context["symptoms"],
        assistant_payload={
            "recommendations": result["recommendations"],
            "diagnosis_hint": result["diagnosis_hint"],
        },
    )
    yield {"event": "final", "data": {"status": "success", "kind": "consultation", "result": result}}


def stream_diagnosis_assist(payload: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    yield {"event": "memory_loaded", "data": {"status": "running", "message": "正在加载病历长上下文记忆"}}
    query_text, memory_store, memory_payload, memory_context, messages, context = _diagnosis_prompt_context(payload)
    retrieval = context["retrieval"]
    yield {"event": "rag_retrieved", "data": {"status": "running", "message": "正在检索医学知识库并准备 RAG 上下文"}}
    yield {"event": "llm_generating", "data": {"status": "running", "message": "正在调用 AI 逐字生成辅助诊断建议", "provider": "aliyun_bailian"}}
    stream = _call_bailian_stream(messages)
    try:
        while True:
            next(stream)
    except StopIteration as stop:
        content = stop.value

    result = _base_payload("diagnosis", query_text, retrieval)
    result["llm_context"]["cache_hit"] = False
    result["llm_context"]["cache_backend"] = "stream"
    result["suggestions"] = _ground_suggestions_to_current_input(
        content.get("suggestions"),
        symptoms=str(context["prompt_payload"].get("symptoms") or ""),
        history=str(context["prompt_payload"].get("history") or ""),
        physique=str(context["prompt_payload"].get("physique") or ""),
    )
    result["memory_context"] = memory_context
    for display_text in _display_chunks(_diagnosis_suggestions_display_text(result["suggestions"])):
        yield {"event": "delta", "data": {"status": "streaming", "text": display_text}}
    persist_conversation_turn(
        memory_store,
        memory_payload,
        user_message=context["query_text"],
        assistant_payload={"suggestions": result["suggestions"]},
    )
    yield {"event": "final", "data": {"status": "success", "kind": "diagnosis", "result": result}}
