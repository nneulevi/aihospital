"""Rerank retrieved RAG candidates."""

from __future__ import annotations

from typing import Any

import httpx

from .config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_RERANK_BASE_URL,
    DASHSCOPE_RERANK_MODEL,
    RAG_RERANK_ENABLED,
    RAG_RERANK_PROVIDER,
    RAG_RERANK_TIMEOUT_SECONDS,
    RAG_RERANK_TOP_N,
)


class RerankProviderError(RuntimeError):
    pass


def _similarity_rerank(candidates: list[dict[str, Any]], *, top_n: int) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=lambda item: float(item.get("similarity", 0.0)), reverse=True)
    for item in ranked:
        item["rerank_score"] = float(item.get("similarity", 0.0))
        item["rerank_provider"] = "vector_similarity"
    return ranked[:top_n]


def _dashscope_rerank(query_text: str, candidates: list[dict[str, Any]], *, top_n: int) -> list[dict[str, Any]]:
    if not DASHSCOPE_API_KEY:
        raise RerankProviderError("DASHSCOPE_API_KEY or ALI_BAILIAN_API_KEY is not configured")
    documents = [str(candidate.get("content") or "") for candidate in candidates]
    try:
        with httpx.Client(timeout=RAG_RERANK_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{DASHSCOPE_RERANK_BASE_URL}/api/v1/services/rerank/text-rerank/text-rerank",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_RERANK_MODEL,
                    "input": {"query": query_text, "documents": documents},
                    "parameters": {"return_documents": False, "top_n": min(top_n, len(documents))},
                },
            )
            if response.status_code >= 400:
                raise RerankProviderError(f"DashScope rerank HTTP {response.status_code}: {response.text[:500]}")
            payload = response.json()
        results = payload.get("output", {}).get("results", [])
        if not isinstance(results, list):
            raise ValueError("DashScope rerank response does not contain output.results")
        ranked: list[dict[str, Any]] = []
        for result in results:
            index = int(result.get("index"))
            if index < 0 or index >= len(candidates):
                continue
            item = dict(candidates[index])
            score = result.get("relevance_score", result.get("score", 0.0))
            item["rerank_score"] = float(score)
            item["rerank_provider"] = "dashscope"
            ranked.append(item)
        if not ranked:
            raise ValueError("DashScope rerank returned no ranked candidates")
        return ranked[:top_n]
    except Exception as exc:
        if isinstance(exc, RerankProviderError):
            raise
        raise RerankProviderError(f"DashScope rerank failed: {exc}") from exc


def rerank_candidates(query_text: str, candidates: list[dict[str, Any]], *, top_n: int = RAG_RERANK_TOP_N) -> list[dict[str, Any]]:
    if not candidates:
        return []
    final_top_n = max(1, min(top_n, len(candidates)))
    if not RAG_RERANK_ENABLED:
        return _similarity_rerank(candidates, top_n=final_top_n)
    if RAG_RERANK_PROVIDER == "dashscope":
        return _dashscope_rerank(query_text, candidates, top_n=final_top_n)
    if RAG_RERANK_PROVIDER in {"similarity", "vector_similarity"}:
        return _similarity_rerank(candidates, top_n=final_top_n)
    raise RerankProviderError(f"Unsupported RAG_RERANK_PROVIDER: {RAG_RERANK_PROVIDER}")
