"""LLM provider for report assistance generation."""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from .config import (
    ALI_BAILIAN_API_KEY,
    ALI_BAILIAN_BASE_URL,
    ALI_BAILIAN_MODEL,
    ALI_BAILIAN_TIMEOUT_SECONDS,
    CACHE_LLM_RESPONSE_TTL_SECONDS,
    LLM_ENABLED,
    LLM_PROVIDER,
)

try:
    from ..cache.cache_keys import llm_response_key
    from ..cache.cache_service import clone_json, get_json, set_json
except ImportError:  # pragma: no cover - direct script fallback.
    from cache.cache_keys import llm_response_key  # type: ignore
    from cache.cache_service import clone_json, get_json, set_json  # type: ignore


class LlmProviderError(RuntimeError):
    pass


SYSTEM_PROMPT = (
    "你是头部 CT AI 报告辅助写作模块。只输出合法 JSON，不输出 Markdown。"
    "你不能给出最终诊断，不能使用“确诊”“排除”“无需复核”“无需医生审核”"
    "“自动完成诊断”“最终诊断为”等绝对化表述。"
    "所有结论必须表述为 AI 辅助参考，并明确提示最终结论需医生结合原始影像审核。"
)


def _walk_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        texts: list[str] = []
        for item in value:
            texts.extend(_walk_text(item))
        return texts
    if isinstance(value, dict):
        texts = []
        for item in value.values():
            texts.extend(_walk_text(item))
        return texts
    return []


def _forbidden_hits(content: dict[str, Any], forbidden_terms: list[str]) -> list[str]:
    joined = "\n".join(_walk_text(content))
    return [term for term in forbidden_terms if term and term in joined]


SAFETY_REWRITES = [
    ("不能排除", "仍需结合原始影像与临床信息评估"),
    ("无法排除", "仍需结合原始影像与临床信息评估"),
    ("无需医生审核", "仍需医生审核"),
    ("无需复核", "仍需医生复核"),
    ("自动完成诊断", "生成辅助报告草稿"),
    ("最终诊断为", "AI 辅助提示"),
    ("确诊为", "AI 辅助提示"),
    ("确诊", "提示"),
    ("排除", "未见明确提示"),
]


def _sanitize_safety_text(value: Any, rewrites: list[dict[str, str]]) -> Any:
    if isinstance(value, str):
        updated = value
        for source, replacement in SAFETY_REWRITES:
            if source in updated:
                updated = updated.replace(source, replacement)
                rewrites.append({"source": source, "replacement": replacement})
        return updated
    if isinstance(value, list):
        return [_sanitize_safety_text(item, rewrites) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_safety_text(item, rewrites) for key, item in value.items()}
    return value


def generate_report_assist_with_llm(
    *,
    model_results: dict[str, Any],
    rag_context: dict[str, Any],
    safety_constraints: dict[str, Any],
    output_schema: dict[str, Any],
) -> dict[str, Any]:
    if not LLM_ENABLED or LLM_PROVIDER == "rule_template":
        return {
            "status": "disabled",
            "provider": "rule_template",
            "model": None,
            "content": None,
            "error_message": None,
        }
    if LLM_PROVIDER != "aliyun_bailian":
        raise LlmProviderError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
    if not ALI_BAILIAN_API_KEY:
        raise LlmProviderError("ALI_BAILIAN_API_KEY is not configured")
    prompt_payload = {
        "model_results": model_results,
        "rag_context": rag_context,
        "safety_constraints": safety_constraints,
        "output_schema": output_schema,
    }
    forbidden_terms = [str(term) for term in safety_constraints.get("forbidden_terms", [])]
    cache_key = llm_response_key(
        "report_assist",
        {
            "provider": LLM_PROVIDER,
            "model": ALI_BAILIAN_MODEL,
            "prompt_payload": prompt_payload,
        },
    )
    cache_hit, cached = get_json(cache_key)
    if cache_hit and isinstance(cached, dict):
        parsed_content = clone_json(cached)
        if isinstance(parsed_content, dict):
            safety_rewrites: list[dict[str, str]] = []
            hits = _forbidden_hits(parsed_content, forbidden_terms)
            if hits:
                parsed_content = _sanitize_safety_text(parsed_content, safety_rewrites)
                hits = _forbidden_hits(parsed_content, forbidden_terms)
            if hits:
                raise LlmProviderError(f"Cached LLM output failed safety validation: forbidden_terms={','.join(hits)}")
            return {
                "status": "success",
                "provider": "aliyun_bailian",
                "model": ALI_BAILIAN_MODEL,
                "content": parsed_content,
                "safety_rewrites": safety_rewrites,
                "cache_hit": True,
                "cache_backend": "redis",
                "error_message": None,
            }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
    ]
    try:
        with httpx.Client(timeout=ALI_BAILIAN_TIMEOUT_SECONDS) as client:
            parsed_content: Optional[dict[str, Any]] = None
            hits: list[str] = []
            for attempt in range(2):
                response = client.post(
                    f"{ALI_BAILIAN_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {ALI_BAILIAN_API_KEY}"},
                    json={
                        "model": ALI_BAILIAN_MODEL,
                        "messages": messages,
                        "temperature": 0.2,
                    },
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("LLM response content must be a JSON object")
                parsed_content = parsed
                hits = _forbidden_hits(parsed_content, forbidden_terms)
                if not hits:
                    break
                if attempt == 0:
                    messages.extend(
                        [
                            {"role": "assistant", "content": json.dumps(parsed_content, ensure_ascii=False)},
                            {
                                "role": "user",
                                "content": (
                                    "上一次 JSON 中仍包含禁止表达："
                                    + "、".join(hits)
                                    + "。请仅返回改写后的 JSON，保留医学谨慎性，"
                                    "用“未见明确提示”“建议结合原始影像审核”“AI 辅助参考”等表述替代。"
                                ),
                            },
                        ]
                    )
            if parsed_content is None:
                raise ValueError("LLM response content is empty")
            safety_rewrites: list[dict[str, str]] = []
            if hits:
                parsed_content = _sanitize_safety_text(parsed_content, safety_rewrites)
                hits = _forbidden_hits(parsed_content, forbidden_terms)
            if hits:
                raise LlmProviderError(f"LLM output failed safety validation after rewriting: forbidden_terms={','.join(hits)}")
            cache_backend = "redis" if set_json(cache_key, parsed_content, CACHE_LLM_RESPONSE_TTL_SECONDS) else "disabled"
        return {
            "status": "success",
            "provider": "aliyun_bailian",
            "model": ALI_BAILIAN_MODEL,
            "content": parsed_content,
            "safety_rewrites": safety_rewrites,
            "cache_hit": False,
            "cache_backend": cache_backend,
            "error_message": None,
        }
    except Exception as exc:
        if isinstance(exc, LlmProviderError):
            raise
        raise LlmProviderError(f"Aliyun Bailian LLM call failed: {exc}") from exc
