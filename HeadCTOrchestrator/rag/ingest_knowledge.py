"""Ingest Markdown knowledge documents into PostgreSQL + pgvector."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import db
from .embedding_provider import embed_text, pgvector_literal
from .knowledge_base import KNOWLEDGE_DIR, KnowledgeChunk, load_knowledge_chunks, load_knowledge_documents


def upsert_chunk(conn: object, chunk: KnowledgeChunk) -> None:
    embedding = pgvector_literal(embed_text(chunk.content))
    sql = """
        INSERT INTO rag_documents (
            source_id, title, doc_type, tags, version, language,
            content, content_hash, embedding, metadata, enabled, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s::jsonb, TRUE, NOW())
        ON CONFLICT (source_id, content_hash)
        DO UPDATE SET
            title = EXCLUDED.title,
            doc_type = EXCLUDED.doc_type,
            tags = EXCLUDED.tags,
            version = EXCLUDED.version,
            language = EXCLUDED.language,
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata,
                enabled = TRUE,
                updated_at = NOW()
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                chunk.source_id,
                chunk.title,
                chunk.doc_type,
                chunk.tags,
                chunk.version,
                chunk.language,
                chunk.content,
                chunk.content_hash,
                embedding,
                json.dumps(chunk.metadata, ensure_ascii=False),
            ),
        )


def ingest_knowledge(knowledge_dir: Path = KNOWLEDGE_DIR, *, initialize_schema: bool = True) -> dict[str, object]:
    documents = load_knowledge_documents(knowledge_dir)
    chunks = load_knowledge_chunks(knowledge_dir)
    if not db.is_configured():
        raise RuntimeError("RAG_DB_DSN is not configured; pgvector ingestion requires a database DSN")
    if initialize_schema:
        db.initialize_schema()
    with db.connect() as conn:
        source_ids = [document.source_id for document in documents]
        if source_ids:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE rag_documents
                    SET enabled = FALSE, updated_at = NOW()
                    WHERE metadata->>'retrieval_unit' IS DISTINCT FROM 'chunk'
                       OR source_id = ANY(%s)
                       OR metadata->>'source_document_id' = ANY(%s)
                    """,
                    (source_ids, source_ids),
                )
        for chunk in chunks:
            upsert_chunk(conn, chunk)
        conn.commit()
    return {"status": "success", "document_count": len(documents), "chunk_count": len(chunks)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest RAG Markdown knowledge documents into pgvector.")
    parser.add_argument("--knowledge-dir", type=Path, default=KNOWLEDGE_DIR)
    parser.add_argument("--skip-schema", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = ingest_knowledge(args.knowledge_dir, initialize_schema=not args.skip_schema)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
