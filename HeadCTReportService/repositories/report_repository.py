"""Transactional PostgreSQL repository for report lifecycle data."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Optional

from psycopg.types.json import Jsonb

from ..db import Database
from ..exceptions import ReportServiceError, conflict, not_found


def new_id() -> str:
    return str(uuid.uuid4())


def report_uuid(value: Any) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ReportServiceError("INVALID_REPORT_ID", "report_id 必须是有效 UUID", 400) from exc


def content_hash(findings: str, impression: str, recommendations: str) -> str:
    raw = json.dumps(
        {"findings": findings, "impression": impression, "recommendations": recommendations},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class PostgresReportRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _audit(
        cursor: Any,
        *,
        actor_id: str,
        actor_role: str,
        action: str,
        target_type: str,
        target_id: str,
        request_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        before_hash: Optional[str] = None,
        after_hash: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO report_audit_events (
                actor_id, actor_role, action, target_type, target_id, request_id,
                client_ip, before_hash, after_hash, metadata_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                actor_id,
                actor_role,
                action,
                target_type,
                target_id,
                request_id,
                client_ip,
                before_hash,
                after_hash,
                Jsonb(metadata or {}),
            ),
        )

    @staticmethod
    def _report_query() -> str:
        return """
            SELECT
                r.*, e.order_id, e.study_id, e.accession_number, e.patient_id,
                e.patient_name, e.department, e.ordering_doctor_id, e.study_instance_uid,
                e.status AS examination_status,
                v.version_number, v.findings, v.impression, v.recommendations,
                v.editor_id, v.change_reason, v.source_type, v.content_hash,
                s.orchestrator_task_id, s.pipeline_version, s.model_versions,
                s.quality_control_json, s.lesion_analysis_json, s.report_assist_json,
                s.rag_references_json, s.deployment_mode
            FROM medical_reports r
            JOIN examination_orders e ON e.id = r.examination_order_id
            JOIN ai_analysis_snapshots s ON s.id = r.ai_snapshot_id
            JOIN medical_report_versions v ON v.id = r.current_version_id
        """

    def register_examination(self, payload: dict[str, Any], actor: dict[str, str]) -> dict[str, Any]:
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM examination_orders WHERE order_id = %s OR study_id = %s FOR UPDATE",
                    (payload["order_id"], payload["study_id"]),
                )
                existing = cursor.fetchone()
                if existing:
                    if existing["order_id"] != payload["order_id"] or existing["study_id"] != payload["study_id"]:
                        raise conflict("EXAMINATION_ID_MISMATCH", "order_id 或 study_id 已绑定到其他检查")
                    return dict(existing)
                examination_id = new_id()
                cursor.execute(
                    """
                    INSERT INTO examination_orders (
                        id, order_id, study_id, accession_number, patient_id, patient_name,
                        department, ordering_doctor_id, study_instance_uid, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ordered')
                    RETURNING *
                    """,
                    (
                        examination_id,
                        payload["order_id"],
                        payload["study_id"],
                        payload.get("accession_number"),
                        payload["patient_id"],
                        payload.get("patient_name"),
                        payload.get("department"),
                        payload.get("ordering_doctor_id"),
                        payload.get("study_instance_uid"),
                    ),
                )
                row = cursor.fetchone()
                self._audit(
                    cursor,
                    actor_id=actor["actor_id"], actor_role=actor["role"],
                    action="examination_registered", target_type="examination", target_id=examination_id,
                )
            conn.commit()
        return dict(row)

    def find_examination_by_study(self, study_id: str) -> dict[str, Any]:
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM examination_orders WHERE study_id = %s", (study_id,))
                row = cursor.fetchone()
        if not row:
            raise not_found("EXAMINATION_NOT_FOUND", "检查记录不存在")
        return dict(row)

    def find_by_task_or_idempotency(self, task_id: str, idempotency_key: Optional[str]) -> Optional[dict[str, Any]]:
        query = self._report_query() + " WHERE s.orchestrator_task_id = %s"
        params: list[Any] = [task_id]
        if idempotency_key:
            query += " OR r.idempotency_key = %s"
            params.append(idempotency_key)
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
        return dict(row) if row else None

    def create_from_analysis(
        self,
        *,
        examination: dict[str, Any],
        snapshot: dict[str, Any],
        report: dict[str, Any],
        version: dict[str, Any],
        actor: dict[str, str],
        idempotency_key: Optional[str],
        request_id: Optional[str],
        client_ip: Optional[str],
    ) -> dict[str, Any]:
        examination_id = new_id()
        snapshot_id = new_id()
        report_id = new_id()
        version_id = new_id()
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM examination_orders WHERE order_id = %s OR study_id = %s FOR UPDATE",
                    (examination["order_id"], examination["study_id"]),
                )
                existing_exam = cursor.fetchone()
                if existing_exam:
                    if existing_exam["order_id"] != examination["order_id"] or existing_exam["study_id"] != examination["study_id"]:
                        raise conflict("EXAMINATION_ID_MISMATCH", "order_id 或 study_id 已绑定到其他检查")
                    if existing_exam["patient_id"] != examination["patient_id"]:
                        raise conflict("EXAMINATION_ID_MISMATCH", "检查记录与患者标识不一致")
                    examination_id = str(existing_exam["id"])
                    cursor.execute(
                        self._report_query() + " WHERE r.examination_order_id = %s",
                        (examination_id,),
                    )
                    existing_report = cursor.fetchone()
                    if existing_report:
                        return dict(existing_report)
                else:
                    cursor.execute(
                        """
                        INSERT INTO examination_orders (
                            id, order_id, study_id, accession_number, patient_id, patient_name,
                            department, ordering_doctor_id, study_instance_uid, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'reporting')
                        """,
                        (
                            examination_id, examination["order_id"], examination["study_id"],
                            examination.get("accession_number"), examination["patient_id"],
                            examination.get("patient_name"), examination.get("department"),
                            examination.get("ordering_doctor_id"), examination.get("study_instance_uid"),
                        ),
                    )
                cursor.execute(
                    """
                    INSERT INTO ai_analysis_snapshots (
                        id, examination_order_id, orchestrator_task_id, pipeline_version,
                        model_versions, quality_control_json, lesion_analysis_json,
                        report_assist_json, rag_references_json, source_result_hash, deployment_mode
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        snapshot_id, examination_id, snapshot["orchestrator_task_id"],
                        snapshot.get("pipeline_version"), Jsonb(snapshot.get("model_versions") or {}),
                        Jsonb(snapshot.get("quality_control") or {}), Jsonb(snapshot.get("lesion_analysis") or {}),
                        Jsonb(snapshot.get("report_assist") or {}), Jsonb(snapshot.get("rag_references") or []),
                        snapshot["source_result_hash"], snapshot["deployment_mode"],
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO medical_reports (
                        id, examination_order_id, ai_snapshot_id, status, version_lock,
                        idempotency_key, assigned_doctor_id
                    ) VALUES (%s, %s, %s, 'draft', 1, %s, %s)
                    """,
                    (report_id, examination_id, snapshot_id, idempotency_key, report.get("assigned_doctor_id")),
                )
                version_digest = content_hash(version["findings"], version["impression"], version["recommendations"])
                cursor.execute(
                    """
                    INSERT INTO medical_report_versions (
                        id, report_id, version_number, findings, impression, recommendations,
                        editor_id, change_reason, source_type, content_hash
                    ) VALUES (%s, %s, 1, %s, %s, %s, %s, %s, 'ai_draft', %s)
                    """,
                    (
                        version_id, report_id, version["findings"], version["impression"],
                        version["recommendations"], actor["actor_id"], "由 AI 分析结果生成初始草稿", version_digest,
                    ),
                )
                cursor.execute(
                    "UPDATE medical_reports SET current_version_id = %s WHERE id = %s",
                    (version_id, report_id),
                )
                cursor.execute(
                    "UPDATE examination_orders SET status = 'reporting', updated_at = NOW() WHERE id = %s",
                    (examination_id,),
                )
                self._audit(
                    cursor,
                    actor_id=actor["actor_id"], actor_role=actor["role"], action="report_created_from_ai",
                    target_type="report", target_id=report_id, request_id=request_id, client_ip=client_ip,
                    after_hash=version_digest,
                    metadata={"orchestrator_task_id": snapshot["orchestrator_task_id"], "version_number": 1},
                )
            conn.commit()
        return self.get_report(report_id)

    def get_report(self, report_id: str) -> dict[str, Any]:
        report_id = report_uuid(report_id)
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(self._report_query() + " WHERE r.id = %s", (report_id,))
                row = cursor.fetchone()
        if not row:
            raise not_found("REPORT_NOT_FOUND", "报告不存在")
        return dict(row)

    def list_reports(
        self,
        *,
        status: Optional[str] = None,
        doctor_id: Optional[str] = None,
        department: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = self._report_query() + " WHERE TRUE"
        params: list[Any] = []
        if status:
            query += " AND r.status = %s"
            params.append(status)
        if doctor_id:
            query += " AND (r.assigned_doctor_id = %s OR r.reviewer_doctor_id = %s OR r.signed_by = %s)"
            params.extend([doctor_id, doctor_id, doctor_id])
        if department:
            query += " AND e.department = %s"
            params.append(department)
        query += " ORDER BY r.updated_at DESC LIMIT %s"
        params.append(limit)
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def list_versions(self, report_id: str) -> list[dict[str, Any]]:
        report_id = report_uuid(report_id)
        self.get_report(report_id)
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM medical_report_versions WHERE report_id = %s ORDER BY version_number DESC",
                    (report_id,),
                )
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def list_audit_events(self, report_id: str) -> list[dict[str, Any]]:
        report_id = report_uuid(report_id)
        self.get_report(report_id)
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM report_audit_events
                    WHERE target_type = 'report' AND target_id = %s
                    ORDER BY created_at DESC
                    """,
                    (report_id,),
                )
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update_draft(
        self,
        report_id: str,
        payload: dict[str, Any],
        actor: dict[str, str],
        request_id: Optional[str],
        client_ip: Optional[str],
    ) -> dict[str, Any]:
        report_id = report_uuid(report_id)
        allowed = {"draft", "revision_required", "amendment_draft"}
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM medical_reports WHERE id = %s FOR UPDATE", (report_id,))
                report = cursor.fetchone()
                if not report:
                    raise not_found("REPORT_NOT_FOUND", "报告不存在")
                if report["status"] not in allowed:
                    raise conflict("REPORT_STATE_CONFLICT", "当前报告状态不允许编辑", status=report["status"])
                if report["version_lock"] != payload["expected_version"]:
                    raise conflict(
                        "REPORT_VERSION_CONFLICT", "报告已被其他用户更新",
                        expected=payload["expected_version"], actual=report["version_lock"],
                    )
                cursor.execute("SELECT * FROM medical_report_versions WHERE id = %s", (report["current_version_id"],))
                previous = cursor.fetchone()
                next_version = report["version_lock"] + 1
                version_id = new_id()
                digest = content_hash(payload["findings"], payload["impression"], payload.get("recommendations") or "")
                source_type = "amendment" if report["status"] == "amendment_draft" else "doctor_edit"
                cursor.execute(
                    """
                    INSERT INTO medical_report_versions (
                        id, report_id, version_number, findings, impression, recommendations,
                        editor_id, change_reason, source_type, content_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        version_id, report_id, next_version, payload["findings"], payload["impression"],
                        payload.get("recommendations") or "", actor["actor_id"], payload.get("change_reason"),
                        source_type, digest,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE medical_reports
                    SET current_version_id = %s, version_lock = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (version_id, next_version, report_id),
                )
                self._audit(
                    cursor,
                    actor_id=actor["actor_id"], actor_role=actor["role"], action="report_version_created",
                    target_type="report", target_id=report_id, request_id=request_id, client_ip=client_ip,
                    before_hash=previous["content_hash"], after_hash=digest,
                    metadata={"version_number": next_version, "source_type": source_type},
                )
            conn.commit()
        return self.get_report(report_id)

    def transition(
        self,
        report_id: str,
        *,
        expected_statuses: set[str],
        target_status: str,
        actor: dict[str, str],
        action: str,
        decision: Optional[str] = None,
        comment: Optional[str] = None,
        request_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> dict[str, Any]:
        report_id = report_uuid(report_id)
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM medical_reports WHERE id = %s FOR UPDATE", (report_id,))
                report = cursor.fetchone()
                if not report:
                    raise not_found("REPORT_NOT_FOUND", "报告不存在")
                if report["status"] not in expected_statuses:
                    raise conflict("REPORT_STATE_CONFLICT", "当前报告状态不允许执行该操作", status=report["status"])
                fields = ["status = %s", "updated_at = NOW()"]
                params: list[Any] = [target_status]
                if action in {"report_approved", "revision_requested"}:
                    fields.append("reviewer_doctor_id = %s")
                    params.append(actor["actor_id"])
                if action == "report_signed":
                    fields.extend(["signed_by = %s", "signed_at = NOW()"])
                    params.append(actor["actor_id"])
                if action == "report_released":
                    fields.append("released_at = NOW()")
                params.append(report_id)
                cursor.execute(f"UPDATE medical_reports SET {', '.join(fields)} WHERE id = %s", params)
                if decision:
                    cursor.execute(
                        """
                        INSERT INTO report_reviews (
                            id, report_id, report_version_id, reviewer_id, decision, comment
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (new_id(), report_id, report["current_version_id"], actor["actor_id"], decision, comment),
                    )
                self._audit(
                    cursor,
                    actor_id=actor["actor_id"], actor_role=actor["role"], action=action,
                    target_type="report", target_id=report_id, request_id=request_id, client_ip=client_ip,
                    metadata={"from_status": report["status"], "to_status": target_status, "comment": comment},
                )
                if action == "report_released":
                    cursor.execute(
                        self._report_query() + " WHERE r.id = %s",
                        (report_id,),
                    )
                    released = json.loads(json.dumps(dict(cursor.fetchone()), ensure_ascii=False, default=str))
                    outbox_id = new_id()
                    cursor.execute(
                        """
                        INSERT INTO report_outbox_events (id, report_id, event_type, payload_json)
                        VALUES (%s, %s, 'medical_report.released', %s)
                        ON CONFLICT (report_id, event_type) DO NOTHING
                        """,
                        (outbox_id, report_id, Jsonb(released)),
                    )
                    cursor.execute(
                        "UPDATE examination_orders SET status = 'reported', updated_at = NOW() WHERE id = %s",
                        (report["examination_order_id"],),
                    )
            conn.commit()
        return self.get_report(report_id)

    def create_amendment(
        self,
        report_id: str,
        payload: dict[str, Any],
        actor: dict[str, str],
        request_id: Optional[str],
        client_ip: Optional[str],
    ) -> dict[str, Any]:
        report_id = report_uuid(report_id)
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM medical_reports WHERE id = %s FOR UPDATE", (report_id,))
                report = cursor.fetchone()
                if not report:
                    raise not_found("REPORT_NOT_FOUND", "报告不存在")
                if report["status"] != "released":
                    raise conflict("REPORT_STATE_CONFLICT", "只有已发布报告可以创建补充报告", status=report["status"])
                cursor.execute("SELECT * FROM medical_report_versions WHERE id = %s", (report["current_version_id"],))
                previous = cursor.fetchone()
                next_version = report["version_lock"] + 1
                version_id = new_id()
                digest = content_hash(payload["findings"], payload["impression"], payload.get("recommendations") or "")
                cursor.execute(
                    """
                    INSERT INTO medical_report_versions (
                        id, report_id, version_number, findings, impression, recommendations,
                        editor_id, change_reason, source_type, content_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'amendment', %s)
                    """,
                    (
                        version_id, report_id, next_version, payload["findings"], payload["impression"],
                        payload.get("recommendations") or "", actor["actor_id"], payload["reason"], digest,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE medical_reports SET current_version_id = %s, version_lock = %s,
                        status = 'amendment_draft', signed_by = NULL, signed_at = NULL,
                        released_at = NULL, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (version_id, next_version, report_id),
                )
                cursor.execute(
                    "DELETE FROM report_outbox_events WHERE report_id = %s AND event_type = 'medical_report.released'",
                    (report_id,),
                )
                self._audit(
                    cursor,
                    actor_id=actor["actor_id"], actor_role=actor["role"], action="amendment_created",
                    target_type="report", target_id=report_id, request_id=request_id, client_ip=client_ip,
                    before_hash=previous["content_hash"], after_hash=digest,
                    metadata={"version_number": next_version, "reason": payload["reason"]},
                )
            conn.commit()
        return self.get_report(report_id)

    def pending_outbox(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM report_outbox_events
                    WHERE status IN ('pending', 'failed') AND next_attempt_at <= NOW()
                    ORDER BY created_at LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def mark_outbox_delivered(self, event_id: str, report_id: str, external_document_id: str) -> None:
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE report_outbox_events SET status = 'delivered', delivered_at = NOW(),
                        external_document_id = %s, attempts = attempts + 1, last_error = NULL
                    WHERE id = %s
                    """,
                    (external_document_id, event_id),
                )
                cursor.execute(
                    "UPDATE medical_reports SET external_document_id = %s, updated_at = NOW() WHERE id = %s",
                    (external_document_id, report_id),
                )
            conn.commit()

    def mark_outbox_failed(self, event_id: str, error: str) -> None:
        with self.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE report_outbox_events SET status = 'failed', attempts = attempts + 1,
                        last_error = %s,
                        next_attempt_at = NOW() + (LEAST(POWER(2, attempts + 1), 300) * INTERVAL '1 second')
                    WHERE id = %s
                    """,
                    (error[:2000], event_id),
                )
            conn.commit()
