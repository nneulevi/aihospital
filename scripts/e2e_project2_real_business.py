"""Run a Project2-first real business end-to-end workflow.

The script exercises the main platform API, not only the AI microservices:

1. Seed one outpatient CT business context in the Project2 database.
2. Call AI consultation triage through Project2.
3. Call AI diagnosis suggestions through Project2.
4. Upload a head CT NIfTI file through Project2.
5. Trigger image analysis through Project2, which calls Orchestrator -> Filter -> Lesion -> RAG/LLM.
6. Generate an AI report through Project2, which calls HeadCTReportService.
7. Verify persisted Project2 rows and downstream report/EMR service health.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

from project2_db_env import get_project2_db_dsn


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CT = Path(os.getenv("HEADCT_E2E_SAMPLE_CT", ROOT / "testdata" / "headct" / "head_ct_positive_case.nii.gz"))
PROJECT2 = os.getenv("PROJECT2_BASE_URL", "http://127.0.0.1:8092")
ORCHESTRATOR = os.getenv("ORCHESTRATOR_BASE_URL", "http://127.0.0.1:8010")
REPORT = os.getenv("REPORT_BASE_URL", "http://127.0.0.1:8030")
EMR = os.getenv("EMR_BASE_URL", "http://127.0.0.1:8040")
DB_DSN = get_project2_db_dsn(ROOT)
EMR_TOKEN = os.getenv("HEADCT_LOCAL_EMR_TOKEN", "headct-local-emr-change-before-production")


def require_ok(response: httpx.Response) -> Any:
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        return {}
    try:
        return response.json()
    except json.JSONDecodeError:
        return json.loads(text)


REQUIRED_TABLES = [
    "patient",
    "register",
    "medical_record",
    "check_request",
    "ai_consultation",
    "ai_diagnosis_suggestion",
    "ai_image_file",
    "ai_image_analysis",
    "ai_generated_report",
]


def assert_project2_schema_ready(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = ANY(%s)
            """
            ,
            (REQUIRED_TABLES,),
        )
        existing = {row["table_name"] for row in cur.fetchall()}
        missing = sorted(set(REQUIRED_TABLES) - existing)
        if missing:
            raise RuntimeError(
                "Project2 database schema is incomplete. Missing tables: "
                + ", ".join(missing)
                + ". Run Project2/sql/init_project2_db.ps1 before real business E2E."
            )
        for table_name in ("patient", "register", "medical_record", "check_request"):
            cur.execute("SELECT pg_get_serial_sequence(%s, 'id') AS seq", (table_name,))
            row = cur.fetchone()
            seq = row["seq"] if row else None
            if seq:
                cur.execute(
                    f"SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false)",
                    (seq,),
                )
    conn.commit()


def seed_business_case() -> dict[str, int | str]:
    suffix = uuid.uuid4().hex[:10]
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        assert_project2_schema_ready(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO patient(case_number, real_name, gender, card_number, birthdate, phone, home_address)
                VALUES (%s, %s, %s, %s, DATE '1972-03-18', %s, %s)
                RETURNING id
                """,
                (f"CASE-{suffix}", "E2E HeadCT Patient", "M", f"ID-{suffix}", "13800000000", "E2E ward"),
            )
            patient_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO register(
                    visit_no, patient_id, visit_date, noon, deptment_id, employee_id,
                    regist_level_id, settle_category_id, source_type, queue_no,
                    regist_method, regist_money, visit_state, create_time, update_time
                )
                VALUES (%s, %s, CURRENT_DATE, 'AM', 1, 1, 1, 1, 'OUTPATIENT', 1, 'WINDOW', 0, 'ONGOING', NOW(), NOW())
                RETURNING id
                """,
                (f"VISIT-{suffix}", patient_id),
            )
            register_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO medical_record(
                    register_id, doctor_id, readme, present, history, physique,
                    proposal, diagnosis, record_status, create_time, update_time
                )
                VALUES (%s, 1, %s, %s, %s, %s, %s, %s, 'TEMPORARY', NOW(), NOW())
                RETURNING id
                """,
                (
                    register_id,
                    "\u6025\u8bca\u5934\u75db\u3001\u5934\u6655\u3001\u6076\u5fc3\uff0c\u5916\u4f24\u540e\u9700\u5b8c\u5584\u5934\u9885 CT\u3002",
                    "\u5934\u90e8\u5916\u4f24\u540e\u5934\u75db\u5934\u6655\u4f34\u6076\u5fc3\uff0c\u9700\u8bc4\u4f30\u9885\u5185\u51fa\u8840\u98ce\u9669\u3002",
                    "\u65e2\u5f80\u65e0\u660e\u786e\u9885\u8111\u624b\u672f\u53f2\u3002",
                    "\u795e\u5fd7\u6e05\u695a\uff0c\u8bc9\u5934\u75db\uff0c\u672a\u89c1\u660e\u663e\u80a2\u4f53\u504f\u762b\u3002",
                    "\u7533\u8bf7\u5934\u9885 CT \u5e73\u626b\u5e76\u8fdb\u884c AI \u8f85\u52a9\u5206\u6790\u3002",
                    "\u5f85\u5f71\u50cf\u68c0\u67e5\u540e\u7efc\u5408\u5224\u65ad\u3002",
                ),
            )
            medical_record_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO check_request(
                    register_id, medical_technology_id, check_info, check_position,
                    creation_time, check_state, check_remark
                )
                VALUES (%s, 1, %s, %s, NOW(), 'CREATED', %s)
                RETURNING id
                """,
                (register_id, "\u5934\u9885 CT \u5e73\u626b", "head", "E2E real business CT order"),
            )
            check_request_id = int(cur.fetchone()["id"])
        conn.commit()
    return {
        "patient_id": patient_id,
        "register_id": register_id,
        "medical_record_id": medical_record_id,
        "check_request_id": check_request_id,
        "case_suffix": suffix,
    }


def fetch_persisted_counts(ids: dict[str, int | str]) -> dict[str, int]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM ai_consultation WHERE patient_id = %s", (ids["patient_id"],))
            consultations = int(cur.fetchone()["n"])
            cur.execute(
                "SELECT COUNT(*) AS n FROM ai_diagnosis_suggestion WHERE medical_record_id = %s",
                (ids["medical_record_id"],),
            )
            diagnosis = int(cur.fetchone()["n"])
            cur.execute("SELECT COUNT(*) AS n FROM ai_image_analysis WHERE check_request_id = %s", (ids["check_request_id"],))
            analyses = int(cur.fetchone()["n"])
            cur.execute("SELECT COUNT(*) AS n FROM ai_generated_report WHERE request_id = %s", (ids["check_request_id"],))
            reports = int(cur.fetchone()["n"])
    return {
        "ai_consultation": consultations,
        "ai_diagnosis_suggestion": diagnosis,
        "ai_image_analysis": analyses,
        "ai_generated_report": reports,
    }


def fetch_latest_project2_report_snapshot(check_request_id: int) -> dict[str, Any]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ai_structured_data
                FROM ai_generated_report
                WHERE request_id = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (check_request_id,),
            )
            row = cur.fetchone()
    if not row or not row["ai_structured_data"]:
        raise RuntimeError("Project2 report snapshot was not persisted")
    return json.loads(row["ai_structured_data"])


def actor(actor_id: str, role: str) -> dict[str, str]:
    return {"X-Actor-Id": actor_id, "X-Actor-Role": role}


def main() -> None:
    if not SAMPLE_CT.exists():
        raise FileNotFoundError(SAMPLE_CT)

    ids = seed_business_case()
    symptoms = "Head trauma followed by headache, dizziness and nausea. Please assess CT urgency and clinical risk."

    with httpx.Client(timeout=360) as client:
        health = {
            "project2": require_ok(client.get(f"{PROJECT2}/actuator/health")).get("status"),
            "orchestrator": require_ok(client.get(f"{ORCHESTRATOR}/api/head-ct-ai/health")).get("status"),
            "report": require_ok(client.get(f"{REPORT}/api/v1/health")).get("status"),
            "emr": require_ok(client.get(f"{EMR}/api/v1/health")).get("status"),
        }

        consultation = require_ok(
            client.post(
                f"{PROJECT2}/api/ai/consultation/triage",
                json={"patientId": ids["patient_id"], "symptoms": symptoms},
            )
        )
        diagnosis = require_ok(
            client.post(
                f"{PROJECT2}/api/ai/diagnosis/suggest",
                json={
                    "medicalRecordId": ids["medical_record_id"],
                    "symptoms": symptoms,
                    "history": "No known prior neurosurgery.",
                    "physique": "Alert, headache, nausea, no obvious limb weakness.",
                },
            )
        )
        with SAMPLE_CT.open("rb") as file_obj:
            upload = require_ok(
                client.post(
                    f"{PROJECT2}/api/ai/image/upload",
                    data={
                        "checkRequestId": str(ids["check_request_id"]),
                        "registerId": str(ids["register_id"]),
                    },
                    files={"file": (SAMPLE_CT.name, file_obj, "application/octet-stream")},
                )
            )
        image_file_id = upload["imageFileId"]
        analysis = require_ok(
            client.post(
                f"{PROJECT2}/api/ai/image/analyze",
                json={"imageFileId": image_file_id, "checkRequestId": ids["check_request_id"]},
            )
        )
        ai_status = analysis.get("aiImagingStatus") or {}
        project_use_status = ai_status.get("projectUseStatus") or ai_status.get("project_use_status")
        if project_use_status != "ready_for_project_demo":
            raise RuntimeError(f"Project2 AI imaging status missing or invalid: {ai_status}")
        if not (ai_status.get("workflowReady") or ai_status.get("workflow_ready")):
            raise RuntimeError(f"Project2 AI imaging workflow is not fully ready: {ai_status}")
        limitations = ai_status.get("limitations") or []
        if limitations:
            raise RuntimeError(f"Project2 AI imaging still reports limitations and cannot be marked deliverable: {limitations}; status={ai_status}")
        lesion_model = ai_status.get("lesionModel") or ai_status.get("lesion_model") or {}
        if lesion_model.get("checkpointFallbackUsed") or lesion_model.get("checkpoint_fallback_used"):
            raise RuntimeError(f"Project2 AI lesion model used checkpoint fallback: {lesion_model}")
        if not (ai_status.get("qualityControlModel") or ai_status.get("quality_control_model")):
            raise RuntimeError(f"Project2 AI quality-control model status is missing: {ai_status}")
        if not (ai_status.get("lesionModel") or ai_status.get("lesion_model")):
            raise RuntimeError(f"Project2 AI lesion model status is missing: {ai_status}")
        report = require_ok(
            client.post(
                f"{PROJECT2}/api/ai/report/generate",
                json={"checkRequestId": ids["check_request_id"], "reportType": "HEAD_CT"},
            )
        )
        report_snapshot = fetch_latest_project2_report_snapshot(int(ids["check_request_id"]))
        report_service_id = str(report_snapshot["id"])
        edited = require_ok(
            client.patch(
                f"{REPORT}/api/v1/reports/{report_service_id}/draft",
                headers=actor("doctor-reporting-001", "reporting_doctor"),
                json={
                    "findings": str(report_snapshot.get("findings") or "") + "\n\u533b\u751f\u5df2\u7ed3\u5408\u539f\u59cb\u5f71\u50cf\u5b8c\u6210\u590d\u6838\u3002",
                    "impression": report_snapshot.get("impression") or "AI \u8f85\u52a9\u62a5\u544a\u5df2\u751f\u6210\uff0c\u6700\u7ec8\u7ed3\u8bba\u9700\u533b\u751f\u5ba1\u6838\u3002",
                    "recommendations": report_snapshot.get("recommendations") or "\u8bf7\u7ed3\u5408\u4e34\u5e8a\u75c7\u72b6\u590d\u67e5\u3002",
                    "expected_version": report_snapshot["version_lock"],
                    "change_reason": "Project2 \u4e3b\u5e73\u53f0\u7aef\u5230\u7aef\u4e1a\u52a1\u9a8c\u6536\uff1a\u62a5\u544a\u533b\u751f\u590d\u6838\u3002",
                },
            )
        )["report"]
        require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/{report_service_id}/submit-review",
                headers=actor("doctor-reporting-001", "reporting_doctor"),
            )
        )
        require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/{report_service_id}/approve",
                headers=actor("doctor-reviewing-001", "reviewing_doctor"),
                json={"comment": "Project2 \u4e3b\u5e73\u53f0\u7aef\u5230\u7aef\u4e1a\u52a1\u9a8c\u6536\u901a\u8fc7\u3002"},
            )
        )
        require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/{report_service_id}/sign",
                headers={
                    **actor("doctor-signing-001", "signing_doctor"),
                    "X-Signature-Confirmation": "confirm",
                },
            )
        )
        released = require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/{report_service_id}/release",
                headers=actor("doctor-signing-001", "signing_doctor"),
            )
        )["report"]
        dispatch = require_ok(
            client.post(
                f"{REPORT}/api/v1/integrations/emr/dispatch",
                headers=actor("emr-bridge", "integration_service"),
            )
        )
        final_report = require_ok(
            client.get(
                f"{REPORT}/api/v1/reports/{report_service_id}",
                headers=actor("doctor-reporting-001", "reporting_doctor"),
            )
        )["report"]
        document_id = final_report.get("external_document_id") or released.get("external_document_id")
        if not document_id:
            raise RuntimeError(f"EMR dispatch did not attach external_document_id: {dispatch}")
        emr_report = require_ok(
            client.get(
                f"{EMR}/api/v1/diagnostic-reports/{document_id}",
                headers={"Authorization": f"Bearer {EMR_TOKEN}"},
            )
        )["report"]

    persisted = fetch_persisted_counts(ids)
    if not consultation.get("consultationId"):
        raise RuntimeError(f"consultation did not return consultationId: {consultation}")
    if not diagnosis.get("suggestions"):
        raise RuntimeError(f"diagnosis suggestions are empty: {diagnosis}")
    if not analysis.get("analysisId"):
        raise RuntimeError(f"analysis did not return analysisId: {analysis}")
    if not report.get("reportId"):
        raise RuntimeError(f"report did not return reportId: {report}")
    for name, count in persisted.items():
        if count <= 0:
            raise RuntimeError(f"{name} was not persisted")

    summary = {
        "status": "success",
        "business_case": ids,
        "health": health,
        "consultation_id": consultation["consultationId"],
        "consultation_recommendation_count": len(consultation.get("recommendations") or []),
        "diagnosis_suggestion_count": len(diagnosis.get("suggestions") or []),
        "image_file_id": image_file_id,
        "analysis_id": analysis["analysisId"],
        "analysis_confidence": analysis.get("confidence"),
        "ai_imaging_project_status": project_use_status,
        "ai_imaging_workflow_ready": ai_status.get("workflowReady") or ai_status.get("workflow_ready"),
        "report_id": report["reportId"],
        "project2_report_status": report.get("status"),
        "report_service_id": report_service_id,
        "report_service_status": final_report.get("status"),
        "report_version_after_review": edited.get("version_number"),
        "emr_document_id": document_id,
        "emr_status": emr_report.get("status"),
        "persisted": persisted,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
