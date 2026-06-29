from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient


if not (os.getenv("REPORT_DB_DSN") or os.getenv("RAG_DB_DSN")):
    pytest.skip("REPORT_DB_DSN or RAG_DB_DSN is required for PostgreSQL integration tests", allow_module_level=True)

from HeadCTReportService import ReportServer as server  # noqa: E402
from HeadCTReportService.db import Database  # noqa: E402
from HeadCTReportService.repositories.report_repository import PostgresReportRepository  # noqa: E402
from HeadCTReportService.services.report_service import ReportService  # noqa: E402


class FakeOrchestratorClient:
    def get_completed_result(self, task_id: str) -> dict[str, Any]:
        return {
            "task_id": task_id,
            "status": "success",
            "module": "head_ct_ai_orchestrator",
            "module_version": "v1.0.0-test",
            "case_context": {"patient_id": None, "study_id": None},
            "pipeline": {"quality_control": "success", "lesion_analysis": "success", "report_assist": "success"},
            "quality_control": {
                "severity": "mild",
                "artifact_detected": True,
                "model_name": "unet2d",
                "model_version": "test-checkpoint",
                "backend": "model",
            },
            "lesion_analysis": {
                "status": "success",
                "results": [
                    {
                        "lesion_type": "intracranial_hemorrhage",
                        "confidence": 0.82,
                        "model_name": "hemorrhage_classifier",
                        "model_version": "test-checkpoint",
                    }
                ],
            },
            "report_assist": {
                "summary": "AI 辅助结果，需医生复核。",
                "suggested_report_sections": {
                    "findings": ["右侧额叶见可疑高密度影。"],
                    "impression": ["右侧额叶出血可能，建议结合原始影像复核。"],
                    "limitations": ["金属伪影可能影响邻近区域观察。"],
                },
                "recommended_actions": [{"code": "review_original_ct", "text": "复核原始 CT。"}],
                "warnings": ["AI 结果仅供辅助参考，最终结论需医生审核。"],
                "requires_doctor_review": True,
                "rag_context": {
                    "enabled": True,
                    "status": "success",
                    "sources": [{"title": "颅内出血报告规范", "chunk_id": "chunk-001"}],
                },
            },
            "warnings": ["AI 结果仅供辅助参考，最终结论需医生审核。"],
        }

    def health(self) -> dict[str, Any]:
        return {"status": "ok"}


class FakeEmrClient:
    enabled = True

    def __init__(self) -> None:
        self.pushed: list[dict[str, Any]] = []

    def push_report(self, payload: dict[str, Any], idempotency_key: str) -> str:
        self.pushed.append({"payload": payload, "idempotency_key": idempotency_key})
        return f"EMR-{len(self.pushed):04d}"

    def health(self) -> dict[str, Any]:
        return {"status": "ok"}


@pytest.fixture()
def client() -> Any:
    database = Database(os.getenv("REPORT_DB_DSN") or os.getenv("RAG_DB_DSN"))
    database.initialize()
    with database.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE report_outbox_events, report_reviews, report_audit_events,
                    medical_report_versions, medical_reports, ai_analysis_snapshots,
                    examination_orders CASCADE
                """
            )
        conn.commit()

    repository = PostgresReportRepository(database)
    fake_orchestrator = FakeOrchestratorClient()
    fake_emr = FakeEmrClient()
    old_values = (
        server.database,
        server.repository,
        server.orchestrator_client,
        server.emr_client,
        server.service,
    )
    server.database = database
    server.repository = repository
    server.orchestrator_client = fake_orchestrator
    server.emr_client = fake_emr
    server.service = ReportService(repository, fake_orchestrator, fake_emr)
    try:
        with TestClient(server.app) as test_client:
            yield test_client, repository, fake_emr
    finally:
        (
            server.database,
            server.repository,
            server.orchestrator_client,
            server.emr_client,
            server.service,
        ) = old_values
        with database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    TRUNCATE TABLE report_outbox_events, report_reviews, report_audit_events,
                        medical_report_versions, medical_reports, ai_analysis_snapshots,
                        examination_orders CASCADE
                    """
                )
            conn.commit()


def headers(role: str, actor_id: str = "doctor-001") -> dict[str, str]:
    return {"X-Actor-Id": actor_id, "X-Actor-Role": role}


def create_report(test_client: TestClient, *, task_id: str | None = None) -> dict[str, Any]:
    suffix = uuid.uuid4().hex[:8]
    task_id = task_id or f"task-{suffix}"
    response = test_client.post(
        f"/api/v1/reports/from-analysis/{task_id}",
        headers={**headers("reporting_doctor"), "Idempotency-Key": f"idem-{task_id}"},
        json={
            "order_id": f"ORDER-{suffix}",
            "study_id": f"STUDY-{suffix}",
            "patient_id": f"PATIENT-{suffix}",
            "accession_number": f"ACC-{suffix}",
            "department": "神经外科",
            "assigned_doctor_id": "doctor-001",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["report"]


def test_full_report_lifecycle_and_emr_outbox(client: Any) -> None:
    test_client, repository, fake_emr = client
    report = create_report(test_client, task_id="task-full-flow")
    report_id = str(report["id"])
    assert report["status"] == "draft"
    assert report["version_number"] == 1
    assert report["rag_references_json"][0]["chunk_id"] == "chunk-001"

    edited = test_client.patch(
        f"/api/v1/reports/{report_id}/draft",
        headers=headers("reporting_doctor"),
        json={
            "findings": "医生复核：右侧额叶见高密度影。",
            "impression": "考虑右侧额叶出血，请结合临床。",
            "recommendations": "建议复查。",
            "expected_version": 1,
            "change_reason": "结合原始影像修订",
        },
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["report"]["version_lock"] == 2

    submitted = test_client.post(f"/api/v1/reports/{report_id}/submit-review", headers=headers("reporting_doctor"))
    assert submitted.json()["report"]["status"] == "pending_review"

    approved = test_client.post(
        f"/api/v1/reports/{report_id}/approve",
        headers=headers("reviewing_doctor", "reviewer-001"),
        json={"comment": "已复核，同意签署。"},
    )
    assert approved.json()["report"]["status"] == "approved"

    signed = test_client.post(
        f"/api/v1/reports/{report_id}/sign",
        headers={**headers("signing_doctor", "signer-001"), "X-Signature-Confirmation": "confirm"},
    )
    assert signed.json()["report"]["status"] == "signed"
    assert signed.json()["report"]["signed_by"] == "signer-001"

    released = test_client.post(f"/api/v1/reports/{report_id}/release", headers=headers("signing_doctor", "signer-001"))
    assert released.status_code == 200, released.text
    assert released.json()["report"]["status"] == "released"
    assert len(repository.pending_outbox()) == 1

    dispatched = test_client.post(
        "/api/v1/integrations/emr/dispatch",
        headers=headers("integration_service", "emr-bridge"),
    )
    assert dispatched.status_code == 200, dispatched.text
    assert dispatched.json()["delivered"] == 1
    assert len(fake_emr.pushed) == 1

    final = test_client.get(f"/api/v1/reports/{report_id}", headers=headers("reporting_doctor"))
    assert final.json()["report"]["external_document_id"] == "EMR-0001"
    versions = test_client.get(f"/api/v1/reports/{report_id}/versions", headers=headers("reporting_doctor"))
    assert len(versions.json()["versions"]) == 2
    audit = test_client.get(f"/api/v1/reports/{report_id}/audit-events", headers=headers("reporting_doctor"))
    actions = {event["action"] for event in audit.json()["events"]}
    assert {"report_created_from_ai", "report_version_created", "report_signed", "report_released"} <= actions


def test_idempotent_creation_returns_same_report(client: Any) -> None:
    test_client, _, _ = client
    suffix = uuid.uuid4().hex[:8]
    body = {
        "order_id": f"ORDER-{suffix}",
        "study_id": f"STUDY-{suffix}",
        "patient_id": f"PATIENT-{suffix}",
    }
    request_headers = {**headers("reporting_doctor"), "Idempotency-Key": "same-business-request"}
    first = test_client.post("/api/v1/reports/from-analysis/task-idempotent", headers=request_headers, json=body)
    second = test_client.post("/api/v1/reports/from-analysis/task-idempotent", headers=request_headers, json=body)
    assert first.status_code == second.status_code == 200
    assert first.json()["report"]["id"] == second.json()["report"]["id"]


def test_optimistic_lock_and_permission_enforcement(client: Any) -> None:
    test_client, _, _ = client
    report = create_report(test_client)
    report_id = str(report["id"])
    payload = {
        "findings": "修订所见",
        "impression": "修订意见",
        "recommendations": "复核",
        "expected_version": 1,
    }
    first = test_client.patch(f"/api/v1/reports/{report_id}/draft", headers=headers("reporting_doctor"), json=payload)
    assert first.status_code == 200
    stale = test_client.patch(f"/api/v1/reports/{report_id}/draft", headers=headers("reporting_doctor"), json=payload)
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "REPORT_VERSION_CONFLICT"
    forbidden = test_client.post(f"/api/v1/reports/{report_id}/approve", headers=headers("reporting_doctor"), json={})
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "REVIEW_PERMISSION_DENIED"


def test_revision_and_amendment_workflows(client: Any) -> None:
    test_client, _, _ = client
    report = create_report(test_client)
    report_id = str(report["id"])
    test_client.post(f"/api/v1/reports/{report_id}/submit-review", headers=headers("reporting_doctor"))
    revision = test_client.post(
        f"/api/v1/reports/{report_id}/request-revision",
        headers=headers("reviewing_doctor", "reviewer-001"),
        json={"comment": "请补充伪影影响范围。"},
    )
    assert revision.status_code == 200
    assert revision.json()["report"]["status"] == "revision_required"

    current = revision.json()["report"]
    test_client.patch(
        f"/api/v1/reports/{report_id}/draft",
        headers=headers("reporting_doctor"),
        json={
            "findings": "已补充伪影影响范围。",
            "impression": current["impression"],
            "recommendations": current["recommendations"],
            "expected_version": current["version_lock"],
        },
    )
    test_client.post(f"/api/v1/reports/{report_id}/submit-review", headers=headers("reporting_doctor"))
    test_client.post(f"/api/v1/reports/{report_id}/approve", headers=headers("reviewing_doctor"), json={})
    test_client.post(
        f"/api/v1/reports/{report_id}/sign",
        headers={**headers("signing_doctor"), "X-Signature-Confirmation": "confirm"},
    )
    test_client.post(f"/api/v1/reports/{report_id}/release", headers=headers("signing_doctor"))

    amendment = test_client.post(
        f"/api/v1/reports/{report_id}/amendments",
        headers=headers("signing_doctor"),
        json={
            "findings": "补充：复查图像显示病灶范围稳定。",
            "impression": "补充意见：病灶范围稳定。",
            "recommendations": "继续临床随访。",
            "reason": "补充复查影像信息",
        },
    )
    assert amendment.status_code == 200, amendment.text
    assert amendment.json()["report"]["status"] == "amendment_draft"
    assert amendment.json()["report"]["source_type"] == "amendment"


def test_examination_registration_and_analysis_binding(client: Any) -> None:
    test_client, _, _ = client
    suffix = uuid.uuid4().hex[:8]
    study_id = f"STUDY-{suffix}"
    registration = test_client.post(
        "/api/v1/integrations/examinations",
        headers=headers("technician", "tech-001"),
        json={
            "order_id": f"ORDER-{suffix}",
            "study_id": study_id,
            "patient_id": f"PATIENT-{suffix}",
            "department": "急诊科",
        },
    )
    assert registration.status_code == 200, registration.text
    binding = test_client.post(
        f"/api/v1/integrations/examinations/{study_id}/analysis",
        headers={**headers("technician", "tech-001"), "Idempotency-Key": f"bind-{suffix}"},
        json={"orchestrator_task_id": f"task-{suffix}", "assigned_doctor_id": "doctor-001"},
    )
    assert binding.status_code == 200, binding.text
    assert binding.json()["report"]["study_id"] == study_id


def test_identity_signature_and_report_id_boundaries(client: Any) -> None:
    test_client, _, _ = client
    missing_identity = test_client.get("/api/v1/reports")
    assert missing_identity.status_code == 401
    assert missing_identity.json()["error"]["code"] == "IDENTITY_REQUIRED"

    invalid_id = test_client.get("/api/v1/reports/not-a-uuid", headers=headers("reporting_doctor"))
    assert invalid_id.status_code == 400
    assert invalid_id.json()["error"]["code"] == "INVALID_REPORT_ID"

    report = create_report(test_client)
    report_id = str(report["id"])
    test_client.post(f"/api/v1/reports/{report_id}/submit-review", headers=headers("reporting_doctor"))
    test_client.post(f"/api/v1/reports/{report_id}/approve", headers=headers("reviewing_doctor"), json={})
    no_confirmation = test_client.post(f"/api/v1/reports/{report_id}/sign", headers=headers("signing_doctor"))
    assert no_confirmation.status_code == 401
    assert no_confirmation.json()["error"]["code"] == "SIGNATURE_CONFIRMATION_REQUIRED"
