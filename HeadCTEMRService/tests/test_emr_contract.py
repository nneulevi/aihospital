from __future__ import annotations

import importlib
import os
import uuid

import pytest
from fastapi.testclient import TestClient


if not (os.getenv("EMR_DB_DSN") or os.getenv("RAG_DB_DSN")):
    pytest.skip("EMR_DB_DSN or RAG_DB_DSN is required", allow_module_level=True)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EMR_DB_DSN", os.getenv("EMR_DB_DSN") or os.getenv("RAG_DB_DSN", ""))
    monkeypatch.setenv("EMR_SERVICE_TOKEN", "test-emr-token")
    import HeadCTEMRService.config as config
    import HeadCTEMRService.EmrServer as server

    importlib.reload(config)
    server = importlib.reload(server)
    server.database.initialize()
    with server.database.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE emr_audit_events, emr_diagnostic_reports CASCADE")
        conn.commit()
    try:
        with TestClient(server.app) as test_client:
            yield test_client, server
    finally:
        with server.database.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE emr_audit_events, emr_diagnostic_reports CASCADE")
            conn.commit()


def auth() -> dict[str, str]:
    return {"Authorization": "Bearer test-emr-token", "Idempotency-Key": "outbox-event-001"}


def payload() -> dict:
    report_id = str(uuid.uuid4())
    return {
        "id": report_id,
        "order_id": "ORDER-001",
        "study_id": "STUDY-001",
        "accession_number": "ACC-001",
        "patient_id": "PATIENT-001",
        "department": "神经外科",
        "status": "released",
        "findings": "右侧额叶见高密度影。",
        "impression": "考虑右侧额叶出血。",
        "recommendations": "建议结合临床复核。",
        "signed_by": "doctor-001",
        "signed_at": "2026-06-15T11:00:00+08:00",
        "released_at": "2026-06-15T11:01:00+08:00",
        "version_number": 2,
        "content_hash": "a" * 64,
        "orchestrator_task_id": "task-001",
        "model_versions": {"orchestrator": "v1.0.0"},
    }


def test_health_authentication_and_idempotent_storage(client) -> None:
    test_client, _ = client
    health = test_client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    unauthorized = test_client.get("/api/v1/diagnostic-reports")
    assert unauthorized.status_code == 401

    report = payload()
    created = test_client.post("/api/v1/diagnostic-reports", headers=auth(), json=report)
    assert created.status_code == 201, created.text
    document_id = created.json()["document_id"]

    repeated = test_client.post("/api/v1/diagnostic-reports", headers=auth(), json=report)
    assert repeated.status_code == 200
    assert repeated.json()["document_id"] == document_id
    assert repeated.json()["created"] is False

    listing = test_client.get("/api/v1/diagnostic-reports", headers={"Authorization": "Bearer test-emr-token"})
    assert listing.status_code == 200
    assert listing.json()["count"] == 1

    detail = test_client.get(
        f"/api/v1/diagnostic-reports/{document_id}",
        headers={"Authorization": "Bearer test-emr-token"},
    )
    assert detail.status_code == 200
    assert detail.json()["report"]["source_report_id"] == report["id"]
    assert detail.json()["audit_events"][0]["action"] == "diagnostic_report_received"


def test_rejects_unsigned_or_non_released_report(client) -> None:
    test_client, _ = client
    report = payload()
    report["status"] = "signed"
    response = test_client.post("/api/v1/diagnostic-reports", headers=auth(), json=report)
    assert response.status_code == 422

