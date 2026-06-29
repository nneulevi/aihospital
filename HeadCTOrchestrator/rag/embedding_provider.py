"""Embedding provider abstraction."""

from __future__ import annotations

import hashlib
import math

import httpx

from .config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_EMBEDDING_BASE_URL,
    DASHSCOPE_EMBEDDING_MODEL,
    DASHSCOPE_EMBEDDING_TIMEOUT_SECONDS,
    RAG_EMBEDDING_DIM,
    RAG_EMBEDDING_PROVIDER,
)


class EmbeddingProviderError(RuntimeError):
    pass


def _deterministic_embed_text(text: str, *, dim: int = RAG_EMBEDDING_DIM) -> list[float]:
    if dim <= 0:
        raise ValueError("embedding dimension must be positive")
    vector = [0.0] * dim
    tokens = [token for token in text.lower().replace("_", " ").split() if token]
    if not tokens:
        tokens = ["empty"]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _dashscope_embed_text(text: str, *, dim: int = RAG_EMBEDDING_DIM) -> list[float]:
    if not DASHSCOPE_API_KEY:
        raise EmbeddingProviderError("DASHSCOPE_API_KEY or ALI_BAILIAN_API_KEY is not configured")
    try:
        with httpx.Client(timeout=DASHSCOPE_EMBEDDING_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{DASHSCOPE_EMBEDDING_BASE_URL}/embeddings",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_EMBEDDING_MODEL,
                    "input": text,
                    "dimensions": dim,
                    "encoding_format": "float",
                },
            )
            if response.status_code >= 400:
                raise EmbeddingProviderError(
                    f"DashScope embedding HTTP {response.status_code}: {response.text[:500]}"
                )
            payload = response.json()
        data = payload.get("data") or []
        if not data or "embedding" not in data[0]:
            raise ValueError("DashScope embedding response does not contain data[0].embedding")
        vector = [float(value) for value in data[0]["embedding"]]
        if len(vector) != dim:
            raise ValueError(f"DashScope embedding dimension mismatch: expected {dim}, got {len(vector)}")
        return vector
    except Exception as exc:
        if isinstance(exc, EmbeddingProviderError):
            raise
        raise EmbeddingProviderError(f"DashScope embedding failed: {exc}") from exc


def embed_text(text: str, *, dim: int = RAG_EMBEDDING_DIM) -> list[float]:
    if RAG_EMBEDDING_PROVIDER == "deterministic":
        return _deterministic_embed_text(text, dim=dim)
    if RAG_EMBEDDING_PROVIDER == "dashscope":
        return _dashscope_embed_text(text, dim=dim)
    raise EmbeddingProviderError(f"Unsupported RAG_EMBEDDING_PROVIDER: {RAG_EMBEDDING_PROVIDER}")


def pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
