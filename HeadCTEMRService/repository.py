"""Persistent EMR diagnostic report repository."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from psycopg.types.json import Jsonb

from .db import Database


class EmrConflict(Exception):
    pass


class EmrRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create_or_get(
        self,
        payload: dict[str, Any],
        idempotency_key: str,
        request_id: Optional[str],
        client_ip: Optional[str],
    ) -> tuple[dict[str, Any], bool]:
        source_report_id = str(payload["id"])
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM emr_diagnostic_reports
                    WHERE idempotency_key = %s OR source_report_id = %s
                    FOR UPDATE
                    """,
                    (idempotency_key, source_report_id),
                )
                existing = cursor.fetchone()
                if existing:
                    if str(existing["source_report_id"]) != source_report_id:
                        raise EmrConflict("Idempotency-Key 已用于其他报告")
                    return dict(existing), False

                document_id = f"DR-{uuid.uuid4().hex.upper()}"
                row_id = str(uuid.uuid4())
                source_payload = json.loads(json.dumps(payload, ensure_ascii=False, default=str))
                cursor.execute(
                    """
                    INSERT INTO emr_diagnostic_reports (
                        id, document_id, idempotency_key, source_report_id, order_id, study_id,
                        accession_number, patient_id, department, status, findings, impression,
                        recommendations, signed_by, signed_at, released_at, content_hash, source_payload
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'final', %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        row_id, document_id, idempotency_key, source_report_id,
                        payload["order_id"], payload["study_id"], payload.get("accession_number"),
                        payload["patient_id"], payload.get("department"), payload["findings"],
                        payload["impression"], payload.get("recommendations") or "", payload["signed_by"],
                        payload["signed_at"], payload.get("released_at"), payload["content_hash"], Jsonb(source_payload),
                    ),
                )
                row = cursor.fetchone()
                cursor.execute(
                    """
                    INSERT INTO emr_audit_events (
                        action, document_id, source_report_id, request_id, client_ip, metadata_json
                    ) VALUES ('diagnostic_report_received', %s, %s, %s, %s, %s)
                    """,
                    (
                        document_id, source_report_id, request_id, client_ip,
                        Jsonb({"version_number": payload["version_number"], "orchestrator_task_id": payload.get("orchestrator_task_id")}),
                    ),
                )
            conn.commit()
        return dict(row), True

    def get(self, document_id: str) -> Optional[dict[str, Any]]:
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM emr_diagnostic_reports WHERE document_id = %s", (document_id,))
                row = cursor.fetchone()
        return dict(row) if row else None

    def list(self, patient_id: Optional[str], study_id: Optional[str], limit: int) -> list[dict[str, Any]]:
        query = "SELECT * FROM emr_diagnostic_reports WHERE TRUE"
        params: list[Any] = []
        if patient_id:
            query += " AND patient_id = %s"
            params.append(patient_id)
        if study_id:
            query += " AND study_id = %s"
            params.append(study_id)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def audit_events(self, document_id: str) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM emr_audit_events WHERE document_id = %s ORDER BY created_at DESC",
                    (document_id,),
                )
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

