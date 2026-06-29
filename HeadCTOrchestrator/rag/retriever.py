"""RAG retrieval against PostgreSQL + pgvector."""

from __future__ import annotations

from typing import Any

from . import db
from .config import CACHE_RAG_RETRIEVAL_TTL_SECONDS, RAG_HNSW_EF_SEARCH, RAG_MIN_SIMILARITY, RAG_RECALL_TOP_N, RAG_TOP_K
from .embedding_provider import embed_text, pgvector_literal
from .reranker import rerank_candidates

try:
    from ..cache.cache_keys import rag_retrieval_key
    from ..cache.cache_service import clone_json, get_json, set_json
except ImportError:  # pragma: no cover - direct script fallback.
    from cache.cache_keys import rag_retrieval_key  # type: ignore
    from cache.cache_service import clone_json, get_json, set_json  # type: ignore


class RagRetrievalError(RuntimeError):
    pass


def retrieve_context(
    query_text: str,
    *,
    filter_tags: list[str] | None = None,
    top_k: int = RAG_TOP_K,
    recall_top_n: int = RAG_RECALL_TOP_N,
    min_similarity: float = RAG_MIN_SIMILARITY,
) -> dict[str, Any]:
    if not db.is_configured():
        raise RagRetrievalError("RAG_DB_DSN is not configured; pgvector is required when RAG is enabled")
    cache_payload = {
        "query_text": query_text,
        "filter_tags": sorted(filter_tags or []),
        "top_k": top_k,
        "recall_top_n": recall_top_n,
        "min_similarity": min_similarity,
        "hnsw_ef_search": RAG_HNSW_EF_SEARCH,
    }
    cache_key = rag_retrieval_key(cache_payload)
    cache_hit, cached = get_json(cache_key)
    if cache_hit and isinstance(cached, dict):
        result = clone_json(cached)
        if isinstance(result, dict):
            result["cache_hit"] = True
            result["cache_backend"] = "redis"
            return result
    try:
        query_vector = pgvector_literal(embed_text(query_text))
        tag_filter = filter_tags if filter_tags else None
        recall_limit = max(top_k, recall_top_n)
        sql = """
            SELECT id, source_id, title, doc_type, tags, content, metadata, 1 - (embedding <=> %s::vector) AS similarity
            FROM rag_documents
            WHERE enabled = TRUE
              AND (%s::text[] IS NULL OR tags && %s::text[])
              AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        with db.connect() as conn:
            with conn.cursor() as cur:
                ef_search = max(1, int(RAG_HNSW_EF_SEARCH))
                cur.execute(f"SET LOCAL hnsw.ef_search = {ef_search}")
                cur.execute(
                    sql,
                    (
                        query_vector,
                        tag_filter,
                        tag_filter,
                        query_vector,
                        min_similarity,
                        query_vector,
                        recall_limit,
                    ),
                )
                rows = cur.fetchall()
        candidates = []
        for row in rows:
            document_id, source_id, title, doc_type, tags, content, metadata, similarity = row
            metadata = metadata or {}
            source_document_id = metadata.get("source_document_id") or source_id
            candidates.append(
                {
                    "id": int(document_id),
                    "source_id": source_document_id,
                    "chunk_source_id": source_id,
                    "chunk_id": metadata.get("chunk_id"),
                    "title": title,
                    "type": doc_type,
                    "tags": list(tags or []),
                    "similarity": float(similarity),
                    "metadata": metadata,
                    "content": content,
                }
            )
        if not candidates:
            raise RagRetrievalError("pgvector retrieval returned no source documents")
        ranked = rerank_candidates(query_text, candidates, top_n=top_k)
        sources = []
        snippets = []
        for item in ranked:
            sources.append(
                {
                    "source_id": item["source_id"],
                    "title": item["title"],
                    "type": item["type"],
                    "tags": item["tags"],
                    "similarity": item["similarity"],
                    "rerank_score": item.get("rerank_score"),
                    "rerank_provider": item.get("rerank_provider"),
                    "chunk_id": item.get("chunk_id"),
                    "metadata": item["metadata"],
                }
            )
            snippets.append(
                {
                    "source_id": item["source_id"],
                    "chunk_id": item.get("chunk_id"),
                    "content": str(item.get("content") or "")[:800],
                }
            )
        result = {
            "status": "success",
            "retrieval_confidence": max(
                (float(source.get("rerank_score") if source.get("rerank_score") is not None else source["similarity"]) for source in sources),
                default=0.0,
            ),
            "sources": sources,
            "snippets": snippets,
            "fallback_reason": None,
            "recall_count": len(candidates),
            "cache_hit": False,
            "cache_backend": "disabled",
        }
        result["cache_backend"] = "redis" if set_json(cache_key, result, CACHE_RAG_RETRIEVAL_TTL_SECONDS) else "disabled"
        return result
    except Exception as exc:
        if isinstance(exc, RagRetrievalError):
            raise
        raise RagRetrievalError(f"pgvector retrieval failed: {exc}") from exc
