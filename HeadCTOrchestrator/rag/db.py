"""PostgreSQL/pgvector access helpers."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import RAG_DB_DSN


SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def psycopg_module():
    try:
        import psycopg  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional package.
        raise RuntimeError("psycopg is not installed; install psycopg[binary] to enable pgvector RAG") from exc
    return psycopg


def is_configured() -> bool:
    return bool(RAG_DB_DSN)


@contextmanager
def connect() -> Iterator[object]:
    if not RAG_DB_DSN:
        raise RuntimeError("RAG_DB_DSN is not configured")
    psycopg = psycopg_module()
    with psycopg.connect(RAG_DB_DSN) as conn:
        yield conn


def initialize_schema() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()


def health() -> dict[str, object]:
    if not RAG_DB_DSN:
        return {"status": "not_configured", "backend": "pgvector"}
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "ok", "backend": "pgvector"}
    except Exception as exc:
        return {"status": "unavailable", "backend": "pgvector", "error": str(exc)}

