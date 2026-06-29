"""PostgreSQL helpers for the EMR service."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from psycopg import Connection, connect
from psycopg.rows import dict_row

from .config import EMR_DB_DSN


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


class Database:
    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = (dsn if dsn is not None else EMR_DB_DSN).strip()

    @contextmanager
    def connection(self) -> Iterator[Connection]:
        if not self.dsn:
            raise RuntimeError("EMR_DB_DSN is not configured")
        with connect(self.dsn, row_factory=dict_row) as conn:
            yield conn

    def initialize(self) -> None:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                    cursor.execute(path.read_text(encoding="utf-8"))
            conn.commit()

    def health(self) -> dict[str, object]:
        if not self.dsn:
            return {"status": "not_configured", "backend": "postgresql"}
        try:
            with self.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT current_database() AS database")
                    row = cursor.fetchone()
            return {"status": "ok", "backend": "postgresql", "database": row["database"]}
        except Exception as exc:
            return {"status": "unavailable", "backend": "postgresql", "error": str(exc)}

