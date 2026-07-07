"""User-perspective acceptance test for the full Project2 + Head CT workflow.

This is stricter than a smoke test. It validates that data shown to each user
role is consistent with the same business case as it moves through the system:

- patient: registration, records, unpaid/paid/refunded orders, dashboard counts
- doctor: queue state transitions, medical orders, diagnosis confirmation
- admin: charge/refund records and daily summary
- medical tech: charged tasks, execution, reports and AI interpretation
- pharmacist: inventory fields, stock movements, dispense and refund
- Head CT AI: Project2 upload/analyze/report -> ReportService -> EMR
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

from project2_db_env import get_project2_db_dsn


ROOT = Path(__file__).resolve().parents[1]
PROJECT2 = os.getenv("PROJECT2_BASE_URL", "http://127.0.0.1:8092")
ORCHESTRATOR = os.getenv("ORCHESTRATOR_BASE_URL", "http://127.0.0.1:8010")
REPORT = os.getenv("REPORT_BASE_URL", "http://127.0.0.1:8030")
EMR = os.getenv("EMR_BASE_URL", "http://127.0.0.1:8040")
EMR_TOKEN = os.getenv("HEADCT_LOCAL_EMR_TOKEN", "headct-local-emr-change-before-production")
SAMPLE_CT = Path(os.getenv("HEADCT_E2E_SAMPLE_CT", ROOT / "testdata" / "headct" / "head_ct_positive_case.nii.gz"))
DB_DSN = get_project2_db_dsn(ROOT)


def unwrap(response: httpx.Response) -> Any:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"HTTP {response.status_code} for {response.request.method} {response.request.url}: {response.text}"
        ) from exc
    if not response.text.strip():
        return None
    return response.json()


def actor(actor_id: str, role: str) -> dict[str, str]:
    return {"X-Actor-Id": actor_id, "X-Actor-Role": role}


def assert_true(condition: bool, message: str, payload: Any = None) -> None:
    if not condition:
        suffix = "" if payload is None else "\n" + json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        raise RuntimeError(message + suffix)


def money(value: Any) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def records(page: dict[str, Any]) -> list[dict[str, Any]]:
    return list(page.get("records") or [])


def require_tables(conn: psycopg.Connection[Any]) -> None:
    required = {
        "department", "employee", "regist_level", "settle_category", "scheduling",
        "patient", "register", "medical_record", "check_request", "inspection_request",
        "disposal_request", "medical_technology", "prescription", "prescription_detail",
        "drug_info", "drug_stock_record", "finance_record", "ai_image_analysis",
        "ai_generated_report", "ai_consultation", "ai_diagnosis_suggestion",
    }
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = ANY(%s)
            """,
            (list(required),),
        )
        existing = {row["table_name"] for row in cur.fetchall()}
        missing = sorted(required - existing)
        if missing:
            raise RuntimeError("Project2 schema missing tables: " + ", ".join(missing))
        for table_name in sorted(required):
            cur.execute("SELECT pg_get_serial_sequence(%s, 'id') AS seq", (table_name,))
            row = cur.fetchone()
            seq = row["seq"] if row else None
            if seq:
                cur.execute(f"SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false)", (seq,))
    conn.commit()


def seed_case() -> dict[str, Any]:
    suffix = uuid.uuid4().hex[:8]
    today = date.today()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        require_tables(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT id, deptment_id, regist_level_id, realname FROM employee WHERE realname = 'doctor' AND role_type = 'DOCTOR' ORDER BY id LIMIT 1")
            doctor = cur.fetchone()
            assert_true(doctor is not None, "demo doctor account does not exist in employee table", {})
            doctor_id = int(doctor["id"])
            dept_id = int(doctor["deptment_id"])
            regist_level_id = int(doctor["regist_level_id"])
            cur.execute("SELECT id, realname FROM employee WHERE realname = 'medicaltech' AND role_type = 'MEDICAL_TECH' ORDER BY id LIMIT 1")
            tech = cur.fetchone()
            assert_true(tech is not None, "demo medicaltech account does not exist in employee table", {})
            tech_employee_id = int(tech["id"])
            cur.execute("SELECT id, realname FROM employee WHERE realname = 'pharmacist' AND role_type = 'PHARMACIST' ORDER BY id LIMIT 1")
            pharmacist = cur.fetchone()
            assert_true(pharmacist is not None, "demo pharmacist account does not exist in employee table", {})
            pharmacist_id = int(pharmacist["id"])
            cur.execute("SELECT id, real_name, gender, card_number, birthdate, phone, home_address FROM patient WHERE phone = '13800001111' ORDER BY id DESC LIMIT 1")
            patient = cur.fetchone()
            assert_true(patient is not None, "demo patient account does not exist in patient table", {})
            cur.execute(
                """
                SELECT id
                FROM settle_category
                WHERE delmark = TRUE
                ORDER BY id
                LIMIT 1
                """,
            )
            settle = cur.fetchone()
            assert_true(settle is not None, "settle category seed data does not exist", {})
            settle_category_id = int(settle["id"])

            chosen_date = today
            chosen_noon = "AM"
            for day_offset in range(0, 30):
                for noon in ["AM", "PM"]:
                    candidate = today + timedelta(days=day_offset)
                    cur.execute(
                        """
                        SELECT COUNT(*) AS cnt
                        FROM register
                        WHERE patient_id = %s
                          AND employee_id = %s
                          AND visit_date = %s
                          AND visit_state IN ('REGISTERED', 'CHECKED_IN', 'DOCTOR_RECEIVED', 'ONGOING', 'CONSULTING')
                        """,
                        (patient["id"], doctor_id, candidate),
                    )
                    if int(cur.fetchone()["cnt"]) == 0:
                        chosen_date = candidate
                        chosen_noon = noon
                        break
                else:
                    continue
                break
            tech_ids: dict[str, int] = {}
            cur.execute("SELECT id FROM medical_technology WHERE tech_code = 'BIZ-CT-HEAD' AND tech_type = 'CHECK' ORDER BY id LIMIT 1")
            check_tech = cur.fetchone()
            assert_true(check_tech is not None, "demo head CT check item does not exist", {})
            tech_ids["CHECK"] = int(check_tech["id"])
            cur.execute("SELECT id FROM medical_technology WHERE tech_code = 'BIZ-BLOOD-ROUTINE' AND tech_type = 'INSPECTION' ORDER BY id LIMIT 1")
            inspection_tech = cur.fetchone()
            assert_true(inspection_tech is not None, "demo blood routine inspection item does not exist", {})
            tech_ids["INSPECTION"] = int(inspection_tech["id"])
            cur.execute(
                """
                SELECT id
                FROM medical_technology
                WHERE tech_type = 'DISPOSAL'
                  AND COALESCE(tech_name, '') = '清创换药'
                ORDER BY id
                LIMIT 1
                """
            )
            disposal_tech = cur.fetchone()
            assert_true(disposal_tech is not None, "demo disposal item does not exist", {})
            tech_ids["DISPOSAL"] = int(disposal_tech["id"])
            cur.execute(
                """
                SELECT id, drug_name, stock_num
                FROM drug_info
                WHERE drug_code = 'BIZ-DRUG-MANNITOL'
                  AND stock_num >= 20
                ORDER BY id
                LIMIT 1
                """
            )
            drug = cur.fetchone()
            assert_true(drug is not None, "demo formal drug with enough stock does not exist", {})
            drug_id = int(drug["id"])
            drug_name = drug["drug_name"]
            drug_initial_stock = int(drug["stock_num"])
        conn.commit()
    return {
        "suffix": suffix,
        "today": today.isoformat(),
        "visit_date": chosen_date.isoformat(),
        "noon": chosen_noon,
        "dept_id": dept_id,
        "doctor_id": doctor_id,
        "doctor_name": doctor["realname"],
        "tech_employee_id": tech_employee_id,
        "tech_employee_name": tech["realname"],
        "pharmacist_id": pharmacist_id,
        "pharmacist_name": pharmacist["realname"],
        "patient_id": int(patient["id"]),
        "patient_name": patient["real_name"],
        "patient_gender": patient["gender"],
        "patient_card_number": patient["card_number"],
        "patient_birthdate": patient["birthdate"].isoformat(),
        "patient_phone": patient["phone"],
        "patient_home_address": patient["home_address"] or "Project2 demo patient address",
        "regist_level_id": regist_level_id,
        "settle_category_id": settle_category_id,
        "check_tech_id": tech_ids["CHECK"],
        "inspection_tech_id": tech_ids["INSPECTION"],
        "disposal_tech_id": tech_ids["DISPOSAL"],
        "drug_id": drug_id,
        "drug_name": drug_name,
        "drug_initial_stock": drug_initial_stock,
    }


def db_patient_id(register_id: int) -> int:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT patient_id FROM register WHERE id = %s", (register_id,))
            return int(cur.fetchone()["patient_id"])


def latest_item_ids(register_id: int) -> dict[str, int]:
    queries = {
        "CHECK": "SELECT id FROM check_request WHERE register_id = %s ORDER BY id DESC LIMIT 1",
        "INSPECTION": "SELECT id FROM inspection_request WHERE register_id = %s ORDER BY id DESC LIMIT 1",
        "DISPOSAL": "SELECT id FROM disposal_request WHERE register_id = %s ORDER BY id DESC LIMIT 1",
    }
    output: dict[str, int] = {}
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for item_type, sql in queries.items():
                cur.execute(sql, (register_id,))
                output[item_type] = int(cur.fetchone()["id"])
    return output


def persisted_ai_counts(check_request_id: int) -> dict[str, int]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM ai_image_analysis WHERE check_request_id = %s", (check_request_id,))
            analyses = int(cur.fetchone()["n"])
            cur.execute("SELECT COUNT(*) AS n FROM ai_generated_report WHERE request_id = %s", (check_request_id,))
            reports = int(cur.fetchone()["n"])
    return {"ai_image_analysis": analyses, "ai_generated_report": reports}


def login_matrix(client: httpx.Client) -> dict[str, Any]:
    roles = [
        ("doctor", "DOCTOR"),
        ("admin", "ADMIN"),
        ("medicaltech", "MEDICAL_TECH"),
        ("pharmacist", "PHARMACIST"),
        ("13800001111", "PATIENT"),
    ]
    result = {}
    for username, role in roles:
        payload = unwrap(client.post(f"{PROJECT2}/api/auth/login", json={"username": username, "password": "123456", "loginType": role}))
        assert_true(bool(payload.get("token")), f"{role} login did not return token", payload)
        assert_true((payload.get("roleType") or payload.get("loginType") or role) == role, f"{role} login returned wrong role", payload)
        result[role] = {"username": username, "id": payload.get("employeeId") or payload.get("patientId")}
    mismatch = client.post(f"{PROJECT2}/api/auth/login", json={"username": "doctor", "password": "123456", "loginType": "PHARMACIST"})
    assert_true(mismatch.status_code >= 400, "doctor should not login as pharmacist", mismatch.text)
    return result


def get_orders(client: httpx.Client, patient_id: int, state: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"patientId": patient_id, "pageNum": 1, "pageSize": 50}
    if state:
        params["orderState"] = state
    return records(unwrap(client.get(f"{PROJECT2}/api/patient/orders", params=params)))


def case_orders(client: httpx.Client, patient_id: int, register_id: int, state: str | None = None) -> list[dict[str, Any]]:
    return [row for row in get_orders(client, patient_id, state) if int(row.get("registerId") or 0) == int(register_id)]


def assert_patient_summary_matches(client: httpx.Client, patient_id: int) -> dict[str, Any]:
    summary = unwrap(client.get(f"{PROJECT2}/api/patient/dashboard/summary", params={"patientId": patient_id}))
    patient_records = unwrap(client.get(f"{PROJECT2}/api/patient/records", params={"patientId": patient_id, "pageNum": 1, "pageSize": 50}))
    unpaid_orders = get_orders(client, patient_id, "UNPAID")
    assert_true(int(summary["recordCount"]) == int(patient_records["total"]), "patient dashboard record count does not match records page", {"summary": summary, "records": patient_records})
    assert_true(int(summary["unpaidOrderCount"]) == len(unpaid_orders), "patient dashboard unpaid count does not match unpaid orders page", {"summary": summary, "unpaid_orders": unpaid_orders})
    assert_true(money(summary["unpaidAmount"]) == sum((money(row.get("amount")) for row in unpaid_orders), Decimal("0.00")), "patient dashboard unpaid amount does not match unpaid order sum", {"summary": summary, "unpaid_orders": unpaid_orders})
    return summary


def assert_fields(row: dict[str, Any], fields: list[str], label: str) -> None:
    missing = [field for field in fields if row.get(field) in (None, "")]
    assert_true(not missing, f"{label} has missing fields: {missing}", row)


def inventory_row(client: httpx.Client, path: str, drug_name: str, drug_id: int) -> dict[str, Any]:
    page = unwrap(client.get(f"{PROJECT2}{path}", params={"drugName": drug_name, "pageNum": 1, "pageSize": 50}))
    row = next((item for item in records(page) if item.get("drugId") == drug_id), None)
    assert_true(row is not None, f"{path} did not return the expected drug", page)
    return row


def prescription_status(prescription_id: int) -> str:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT prescription_status FROM prescription WHERE id = %s", (prescription_id,))
            row = cur.fetchone()
    assert_true(row is not None, "prescription row not found", {"prescriptionId": prescription_id})
    return str(row["prescription_status"])


def db_stock(drug_id: int) -> int:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stock_num FROM drug_info WHERE id = %s", (drug_id,))
            row = cur.fetchone()
    assert_true(row is not None, "drug row not found", {"drugId": drug_id})
    return int(row["stock_num"] or 0)


def db_finance_records(register_id: int) -> list[dict[str, Any]]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, record_no, register_id, item_id, item_type, item_name,
                       amount, charge_method, record_type, operator_name, create_time
                FROM finance_record
                WHERE register_id = %s
                ORDER BY id DESC
                """,
                (register_id,),
            )
            return list(cur.fetchall())


def db_stock_records(drug_id: int, prescription_id: int) -> list[dict[str, Any]]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, drug_id, record_type, quantity, before_stock, after_stock,
                       operator_id, related_prescription_id, reason, create_time
                FROM drug_stock_record
                WHERE drug_id = %s AND (related_prescription_id = %s OR related_prescription_id IS NULL)
                ORDER BY id DESC
                """,
                (drug_id, prescription_id),
            )
            return list(cur.fetchall())


def expect_http_error(response: httpx.Response, label: str) -> None:
    assert_true(response.status_code >= 400, f"{label} should be rejected", {"status": response.status_code, "body": response.text})


def run_headct_report_flow(client: httpx.Client, register_id: int, check_request_id: int) -> dict[str, Any]:
    if not SAMPLE_CT.exists():
        raise FileNotFoundError(SAMPLE_CT)
    with SAMPLE_CT.open("rb") as file_obj:
        upload = unwrap(
            client.post(
                f"{PROJECT2}/api/ai/image/upload",
                data={"checkRequestId": str(check_request_id), "registerId": str(register_id)},
                files={"file": (SAMPLE_CT.name, file_obj, "application/octet-stream")},
            )
        )
    analysis = unwrap(
        client.post(
            f"{PROJECT2}/api/ai/image/analyze",
            json={"imageFileId": upload["imageFileId"], "checkRequestId": check_request_id},
        )
    )
    ai_status = analysis.get("aiImagingStatus") or {}
    assert_true((ai_status.get("projectUseStatus") or ai_status.get("project_use_status")) == "ready_for_project_demo", "AI image status is not project-ready", ai_status)
    assert_true(bool(ai_status.get("workflowReady") or ai_status.get("workflow_ready")), "AI image workflow is not ready", ai_status)
    lesion_model = ai_status.get("lesionModel") or ai_status.get("lesion_model") or {}
    assert_true(not (lesion_model.get("checkpointFallbackUsed") or lesion_model.get("checkpoint_fallback_used")), "lesion model used checkpoint fallback", lesion_model)
    assert_true(analysis.get("positiveProbability") is not None, "analysis does not expose positiveProbability", analysis)
    assert_true(bool(analysis.get("subtypeProbabilities")), "analysis does not expose subtype probabilities", analysis)

    report = unwrap(client.post(f"{PROJECT2}/api/ai/report/generate", json={"checkRequestId": check_request_id, "reportType": "HEAD_CT"}))
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ai_structured_data FROM ai_generated_report
                WHERE request_id = %s ORDER BY id DESC LIMIT 1
                """,
                (check_request_id,),
            )
            snapshot = json.loads(cur.fetchone()["ai_structured_data"])
    report_service_id = str(snapshot["id"])
    edited = unwrap(
        client.patch(
            f"{REPORT}/api/v1/reports/{report_service_id}/draft",
            headers=actor("user-logic-reporting", "reporting_doctor"),
            json={
                "findings": str(snapshot.get("findings") or "") + "\nDoctor reviewed the original CT images.",
                "impression": snapshot.get("impression") or "AI-assisted report generated; final conclusion reviewed by doctor.",
                "recommendations": snapshot.get("recommendations") or "Correlate with clinical symptoms.",
                "expected_version": snapshot["version_lock"],
                "change_reason": "User logic acceptance doctor review.",
            },
        )
    )["report"]
    unwrap(client.post(f"{REPORT}/api/v1/reports/{report_service_id}/submit-review", headers=actor("user-logic-reporting", "reporting_doctor")))
    unwrap(client.post(f"{REPORT}/api/v1/reports/{report_service_id}/approve", headers=actor("user-logic-review", "reviewing_doctor"), json={"comment": "accepted"}))
    unwrap(client.post(f"{REPORT}/api/v1/reports/{report_service_id}/sign", headers={**actor("user-logic-sign", "signing_doctor"), "X-Signature-Confirmation": "confirm"}))
    unwrap(client.post(f"{REPORT}/api/v1/reports/{report_service_id}/release", headers=actor("user-logic-sign", "signing_doctor")))
    unwrap(client.post(f"{REPORT}/api/v1/integrations/emr/dispatch", headers=actor("emr-bridge", "integration_service")))
    final_report = unwrap(client.get(f"{REPORT}/api/v1/reports/{report_service_id}", headers=actor("user-logic-reporting", "reporting_doctor")))["report"]
    document_id = final_report.get("external_document_id")
    assert_true(bool(document_id), "released report was not dispatched to EMR", final_report)
    emr_report = unwrap(client.get(f"{EMR}/api/v1/diagnostic-reports/{document_id}", headers={"Authorization": f"Bearer {EMR_TOKEN}"}))["report"]
    assert_true(emr_report.get("status") == "final", "EMR report is not final", emr_report)
    counts = persisted_ai_counts(check_request_id)
    assert_true(counts["ai_image_analysis"] >= 1 and counts["ai_generated_report"] >= 1, "Project2 AI rows were not persisted", counts)
    return {
        "upload": upload,
        "analysis": analysis,
        "report": report,
        "report_service_id": report_service_id,
        "report_version": edited.get("version_number"),
        "emr_document_id": document_id,
        "persisted_ai": counts,
    }


def main() -> None:
    seed = seed_case()
    patient_name = seed["patient_name"]

    with httpx.Client(timeout=420) as client:
        health = {
            "project2": unwrap(client.get(f"{PROJECT2}/actuator/health")).get("status"),
            "orchestrator": unwrap(client.get(f"{ORCHESTRATOR}/api/head-ct-ai/health")).get("status"),
            "report": unwrap(client.get(f"{REPORT}/api/v1/health")).get("status"),
            "emr": unwrap(client.get(f"{EMR}/api/v1/health")).get("status"),
        }
        assert_true(health["project2"] == "UP" and all(health[name] == "ok" for name in ["orchestrator", "report", "emr"]), "service health check failed", health)
        logins = login_matrix(client)
        assert_true(int(logins["DOCTOR"]["id"]) == int(seed["doctor_id"]), "doctor interaction is not bound to demo doctor account", {"login": logins["DOCTOR"], "seedDoctorId": seed["doctor_id"]})
        assert_true(int(logins["ADMIN"]["id"]) == 18, "admin interaction is not bound to demo admin account", logins["ADMIN"])
        assert_true(int(logins["MEDICAL_TECH"]["id"]) == int(seed["tech_employee_id"]), "medical-tech interaction is not bound to demo medicaltech account", {"login": logins["MEDICAL_TECH"], "seedTechId": seed["tech_employee_id"]})
        assert_true(int(logins["PHARMACIST"]["id"]) == int(seed["pharmacist_id"]), "pharmacy interaction is not bound to demo pharmacist account", {"login": logins["PHARMACIST"], "seedPharmacistId": seed["pharmacist_id"]})
        assert_true(int(logins["PATIENT"]["id"]) == int(seed["patient_id"]), "patient interaction is not bound to demo patient account", {"login": logins["PATIENT"], "seedPatientId": seed["patient_id"]})
        schedule_id = unwrap(
            client.post(
                f"{PROJECT2}/api/schedule/sources",
                json={
                    "doctorId": seed["doctor_id"],
                    "deptId": seed["dept_id"],
                    "scheduleDate": seed["visit_date"],
                    "noon": seed["noon"],
                    "registQuota": 30,
                    "sourceType": "ADMIN_DEMO",
                },
            )
        )
        assert_true(int(schedule_id) > 0, "admin schedule source creation did not return schedule id", {"scheduleId": schedule_id})

        doctors = unwrap(
            client.get(
                f"{PROJECT2}/api/patient/doctors",
                params={"deptId": seed["dept_id"], "visitDate": seed["visit_date"], "noon": seed["noon"], "pageNum": 1, "pageSize": 20},
            )
        )
        doctor_rows = records(doctors)
        selected = next((row for row in doctor_rows if row.get("doctorId") == seed["doctor_id"]), None)
        assert_true(selected is not None and int(selected.get("remainingQuota", 0)) > 0, "scheduled doctor is not visible to patient appointment page", doctors)

        register_id = unwrap(
            client.post(
                f"{PROJECT2}/api/patient/register",
                json={
                    "realName": patient_name,
                    "gender": seed["patient_gender"],
                    "cardNumber": seed["patient_card_number"],
                    "birthdate": seed["patient_birthdate"],
                    "homeAddress": seed["patient_home_address"],
                    "phone": seed["patient_phone"],
                    "deptId": seed["dept_id"],
                    "doctorId": seed["doctor_id"],
                    "visitDate": seed["visit_date"],
                    "noon": seed["noon"],
                    "registLevelId": seed["regist_level_id"],
                    "settleCategoryId": seed["settle_category_id"],
                    "registMethod": "APP",
                },
            )
        )
        patient_id = db_patient_id(int(register_id))
        assert_true(int(patient_id) == int(seed["patient_id"]), "registration did not attach to demo patient account", {"registeredPatientId": patient_id, "demoPatientId": seed["patient_id"]})
        summary_after_register = assert_patient_summary_matches(client, patient_id)
        doctor_queue_params = {
            "doctorId": seed["doctor_id"],
            "visitState": "REGISTERED",
            "visitDate": seed["visit_date"],
            "noon": seed["noon"],
            "pageNum": 1,
            "pageSize": 50,
        }
        doctor_pending = records(unwrap(client.get(f"{PROJECT2}/api/doctor/patients", params=doctor_queue_params)))
        assert_true(any(row.get("registerId") == register_id and row.get("patientName") == patient_name for row in doctor_pending), "new patient is not visible in doctor's pending queue", doctor_pending)

        unwrap(client.put(f"{PROJECT2}/api/doctor/patients/{register_id}/receive"))
        doctor_consulting_params = dict(doctor_queue_params)
        doctor_consulting_params["visitState"] = "DOCTOR_RECEIVED"
        doctor_consulting = records(unwrap(client.get(f"{PROJECT2}/api/doctor/patients", params=doctor_consulting_params)))
        assert_true(any(row.get("registerId") == register_id for row in doctor_consulting), "received patient is not visible in doctor's consulting queue", doctor_consulting)

        unwrap(
            client.post(
                f"{PROJECT2}/api/doctor/medical-record",
                json={
                    "registerId": register_id,
                    "readme": "Head trauma with headache.",
                    "present": "Headache, dizziness and nausea after trauma.",
                    "history": "No known previous neurosurgery.",
                    "physique": "Alert, no obvious limb weakness.",
                    "proposal": "Head CT and observation.",
                    "diagnosis": "Pending imaging review.",
                },
            )
        )
        unwrap(client.post(f"{PROJECT2}/api/doctor/check-request", json={"registerId": register_id, "items": [{"medicalTechnologyId": seed["check_tech_id"], "checkInfo": "Head CT plain scan", "checkPosition": "head"}]}))
        unwrap(client.post(f"{PROJECT2}/api/doctor/inspection-request", json={"registerId": register_id, "items": [{"medicalTechnologyId": seed["inspection_tech_id"], "inspectionInfo": "Blood routine", "inspectionPosition": "blood"}]}))
        unwrap(client.post(f"{PROJECT2}/api/doctor/disposal-request", json={"registerId": register_id, "items": [{"medicalTechnologyId": seed["disposal_tech_id"], "disposalInfo": "Wound care", "disposalPosition": "head"}]}))
        item_ids = latest_item_ids(int(register_id))
        prescription_id = unwrap(
            client.post(
                f"{PROJECT2}/api/doctor/prescription",
                json={
                    "registerId": register_id,
                    "doctorId": seed["doctor_id"],
                    "items": [
                        {
                            "drugId": seed["drug_id"],
                            "usageRoute": "IV",
                            "frequency": "QD",
                            "singleDose": "250ml",
                            "useDays": 1,
                            "drugNumber": 2,
                        }
                    ],
                },
            )
        )

        unpaid_before_charge = case_orders(client, patient_id, register_id, "UNPAID")
        expected_types = {"CHECK", "INSPECTION", "DISPOSAL", "PRESCRIPTION"}
        assert_true({row.get("itemType") for row in unpaid_before_charge}.issuperset(expected_types), "patient unpaid page misses doctor orders", unpaid_before_charge)
        summary_with_unpaid = assert_patient_summary_matches(client, patient_id)
        assert_true(int(summary_with_unpaid["unpaidOrderCount"]) >= len(unpaid_before_charge), "patient dashboard should include all newly created unpaid items", {"summary": summary_with_unpaid, "caseOrders": unpaid_before_charge})

        tech_items = [item_ids["CHECK"], item_ids["INSPECTION"], item_ids["DISPOSAL"]]
        unwrap(client.post(f"{PROJECT2}/api/admin/finance/charge", json={"registerId": register_id, "itemIds": tech_items, "itemTypes": ["CHECK", "INSPECTION", "DISPOSAL"], "chargeMethod": "CASH", "amount": "240.00"}))
        paid_after_tech_charge = case_orders(client, patient_id, register_id, "PAID")
        assert_true({row.get("itemType") for row in paid_after_tech_charge}.issuperset({"CHECK", "INSPECTION", "DISPOSAL"}), "charged medical-tech items are not visible as paid to patient", paid_after_tech_charge)
        summary_after_tech_charge = assert_patient_summary_matches(client, patient_id)
        case_unpaid_after_tech_charge = case_orders(client, patient_id, register_id, "UNPAID")
        assert_true(len(case_unpaid_after_tech_charge) == 1 and case_unpaid_after_tech_charge[0].get("itemType") == "PRESCRIPTION", "only current prescription should remain unpaid after medical-tech charge", {"summary": summary_after_tech_charge, "caseUnpaid": case_unpaid_after_tech_charge})

        tasks = records(unwrap(client.get(f"{PROJECT2}/api/medical-tech/tasks", params={"registerId": register_id, "state": "CHARGED", "pageNum": 1, "pageSize": 20})))
        assert_true(len(tasks) >= 3, "medical-tech workbench cannot see charged tasks", tasks)
        for item_type, item_id, result_text in [
            ("CHECK", item_ids["CHECK"], "Head CT plain scan result entered."),
            ("INSPECTION", item_ids["INSPECTION"], "Blood routine result entered."),
            ("DISPOSAL", item_ids["DISPOSAL"], "Wound care completed."),
        ]:
            unwrap(client.post(f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/execute", json={"executorId": seed["tech_employee_id"], "remark": "execute"}))
            unwrap(client.post(f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/report", json={"reporterId": seed["tech_employee_id"], "result": result_text, "remark": "report"}))
            interpretation = unwrap(client.post(f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/ai-interpret"))
            assert_true(bool(interpretation.get("summary")), "medical-tech AI interpretation has no summary", interpretation)
        check_results = unwrap(client.get(f"{PROJECT2}/api/doctor/check-results/{register_id}"))
        assert_true(bool(check_results.get("checkRequests")) and bool(check_results.get("inspectionRequests")) and bool(check_results.get("disposalRequests")), "doctor cannot see completed medical-tech reports", check_results)

        required_drug_fields = ["drugId", "drugCode", "drugName", "drugFormat", "drugUnit", "drugPrice", "manufacturer", "stockNum"]
        drug_row = inventory_row(client, "/api/drugstore/inventory", seed["drug_name"], seed["drug_id"])
        admin_drug_row = inventory_row(client, "/api/admin/drug/inventory", seed["drug_name"], seed["drug_id"])
        assert_fields(drug_row, required_drug_fields, "drugstore inventory row")
        assert_fields(admin_drug_row, required_drug_fields, "admin inventory row")
        assert_true(
            int(drug_row["stockNum"]) == int(admin_drug_row["stockNum"]) == db_stock(seed["drug_id"]),
            "admin and drugstore inventory are inconsistent before stock movement",
            {"drugstore": drug_row, "admin": admin_drug_row, "dbStock": db_stock(seed["drug_id"])},
        )
        baseline_stock = int(seed["drug_initial_stock"])
        unwrap(client.post(f"{PROJECT2}/api/drugstore/stock/in", json={"drugId": seed["drug_id"], "quantity": 20, "operatorId": seed["pharmacist_id"], "reason": "业务补货入库"}))
        unwrap(client.post(f"{PROJECT2}/api/drugstore/stock/check", json={"drugId": seed["drug_id"], "actualStock": baseline_stock, "operatorId": seed["pharmacist_id"], "reason": "月度盘点校正"}))
        checked_drugstore_row = inventory_row(client, "/api/drugstore/inventory", seed["drug_name"], seed["drug_id"])
        checked_admin_row = inventory_row(client, "/api/admin/drug/inventory", seed["drug_name"], seed["drug_id"])
        assert_true(
            int(checked_drugstore_row["stockNum"]) == int(checked_admin_row["stockNum"]) == baseline_stock == db_stock(seed["drug_id"]),
            "stock check did not synchronize admin, drugstore and database inventory",
            {"drugstore": checked_drugstore_row, "admin": checked_admin_row, "dbStock": db_stock(seed["drug_id"])},
        )
        alerts = records(unwrap(client.get(f"{PROJECT2}/api/drugstore/stock/alerts", params={"threshold": 30, "pageNum": 1, "pageSize": 50})))
        exposed_alerts = [
            row for row in alerts
            if str(row.get("drugCode") or "").startswith("BIZFLOW-")
            or str(row.get("drugName") or "").startswith("业务联动")
            or str(row.get("manufacturer") or "").startswith("业务联动")
        ]
        assert_true(not exposed_alerts, "low-stock alert exposes acceptance-only drug rows", exposed_alerts)
        for alert in alerts:
            assert_fields(alert, required_drug_fields, "low-stock alert row")

        unwrap(client.post(f"{PROJECT2}/api/admin/finance/charge", json={"registerId": register_id, "itemIds": [prescription_id], "itemTypes": ["PRESCRIPTION"], "chargeMethod": "CASH", "amount": "25.00"}))
        summary_after_all_charge = assert_patient_summary_matches(client, patient_id)
        assert_true(not case_orders(client, patient_id, register_id, "UNPAID"), "current registration should have no unpaid orders after all charges", {"summary": summary_after_all_charge, "caseUnpaid": case_orders(client, patient_id, register_id, "UNPAID")})
        pending_dispense = unwrap(client.get(f"{PROJECT2}/api/admin/drug/pending-dispense"))
        assert_true(any(row.get("prescriptionId") == prescription_id for row in pending_dispense), "charged prescription is not visible in pending dispense list", pending_dispense)
        assert_true(prescription_status(prescription_id) == "CHARGED", "prescription status should be CHARGED after prescription charge", {"status": prescription_status(prescription_id)})
        unwrap(client.post(f"{PROJECT2}/api/drugstore/dispense", json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"]}))
        assert_true(prescription_status(prescription_id) == "DISPENSED", "prescription status should be DISPENSED after dispense", {"status": prescription_status(prescription_id)})
        after_dispense_row = inventory_row(client, "/api/drugstore/inventory", seed["drug_name"], seed["drug_id"])
        assert_true(int(after_dispense_row["stockNum"]) == baseline_stock - 2 == db_stock(seed["drug_id"]), "dispense did not deduct stock by prescribed quantity", {"row": after_dispense_row, "dbStock": db_stock(seed["drug_id"]), "baselineStock": baseline_stock})
        pending_refund = unwrap(client.get(f"{PROJECT2}/api/admin/drug/pending-refund"))
        assert_true(any(row.get("prescriptionId") == prescription_id for row in pending_refund), "dispensed prescription is not visible in pending refund list", pending_refund)
        unwrap(client.post(f"{PROJECT2}/api/drugstore/refund", json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"], "refundReason": "患者退药复核"}))
        assert_true(prescription_status(prescription_id) == "REFUNDED", "prescription status should be REFUNDED after drug refund", {"status": prescription_status(prescription_id)})
        after_refund_row = inventory_row(client, "/api/drugstore/inventory", seed["drug_name"], seed["drug_id"])
        after_refund_admin_row = inventory_row(client, "/api/admin/drug/inventory", seed["drug_name"], seed["drug_id"])
        assert_true(
            int(after_refund_row["stockNum"]) == int(after_refund_admin_row["stockNum"]) == baseline_stock == db_stock(seed["drug_id"]),
            "drug refund did not restore stock consistently",
            {"drugstore": after_refund_row, "admin": after_refund_admin_row, "dbStock": db_stock(seed["drug_id"])},
        )
        duplicate_refund = client.post(f"{PROJECT2}/api/drugstore/refund", json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"], "refundReason": "duplicate refund should fail"})
        expect_http_error(duplicate_refund, "duplicate drug refund")
        refunded_orders = case_orders(client, patient_id, register_id, "REFUNDED")
        assert_true(any(row.get("itemType") == "PRESCRIPTION" and row.get("itemId") == prescription_id for row in refunded_orders), "refunded prescription is not visible to patient", refunded_orders)
        stock_records = records(unwrap(client.get(f"{PROJECT2}/api/drugstore/stock/records", params={"drugId": seed["drug_id"], "pageNum": 1, "pageSize": 50})))
        assert_true({"IN", "CHECK", "DISPENSE", "REFUND"}.issubset({row.get("recordType") for row in stock_records}), "drug stock movement history is incomplete", stock_records)
        db_stock_movements = db_stock_records(seed["drug_id"], prescription_id)
        assert_true({"IN", "CHECK", "DISPENSE", "REFUND"}.issubset({row.get("record_type") for row in db_stock_movements}), "database stock movement history is incomplete", db_stock_movements)
        for movement in db_stock_movements:
            assert_fields(movement, ["id", "drug_id", "record_type", "quantity", "before_stock", "after_stock", "operator_id", "create_time"], "database stock movement")

        unwrap(client.put(f"{PROJECT2}/api/doctor/diagnosis/confirm", json={"registerId": register_id, "diagnosis": "Head trauma follow-up", "cure": "Observation and follow-up", "diseaseIds": []}))
        final_record = unwrap(client.get(f"{PROJECT2}/api/patient/records/{register_id}"))
        assert_true(final_record.get("visitState") == "DIAGNOSIS_DONE" and final_record.get("diagnosis") == "Head trauma follow-up", "patient record detail does not reflect confirmed diagnosis", final_record)

        finance_records = records(unwrap(client.get(f"{PROJECT2}/api/admin/finance/records", params={"pageNum": 1, "pageSize": 50})))
        related_finance = [row for row in finance_records if row.get("registerId") == register_id]
        finance_required_fields = ["id", "recordNo", "registerId", "itemId", "itemType", "itemName", "amount", "chargeMethod", "recordType", "createTime", "operatorName"]
        for row in related_finance:
            assert_fields(row, finance_required_fields, "finance API record")
        assert_true({"CHARGE", "REFUND"}.issubset({row.get("recordType") for row in related_finance}), "finance records miss charge/refund entries for the case", related_finance)
        db_related_finance = db_finance_records(register_id)
        assert_true({"CHARGE", "REFUND"}.issubset({row.get("record_type") for row in db_related_finance}), "database finance records miss charge/refund entries for the case", db_related_finance)
        for row in db_related_finance:
            assert_fields(row, ["id", "record_no", "register_id", "item_id", "item_type", "item_name", "amount", "charge_method", "record_type", "operator_name", "create_time"], "database finance record")
        assert_true(
            any(row.get("item_type") == "PRESCRIPTION" and row.get("item_id") == prescription_id and row.get("record_type") == "REFUND" for row in db_related_finance),
            "database finance records do not contain the prescription refund",
            db_related_finance,
        )
        daily = unwrap(client.get(f"{PROJECT2}/api/admin/finance/daily-summary", params={"summaryDate": seed["today"]}))
        assert_true(int(daily.get("chargeCount", 0)) >= 2 and int(daily.get("refundCount", 0)) >= 1, "daily finance summary is inconsistent with performed transactions", daily)

        headct = run_headct_report_flow(client, int(register_id), item_ids["CHECK"])

    summary = {
        "status": "success",
        "health": health,
        "logins": logins,
        "seed": seed,
        "admin_created_schedule_id_for_demo_doctor": schedule_id,
        "register_id": register_id,
        "patient_id": patient_id,
        "demo_account_flow": {
            "adminId": logins["ADMIN"]["id"],
            "patientId": patient_id,
            "doctorId": seed["doctor_id"],
            "doctorName": seed["doctor_name"],
            "visitDate": seed["visit_date"],
            "noon": seed["noon"],
        },
        "patient_summary_after_register": summary_after_register,
        "patient_summary_after_unpaid_created": summary_with_unpaid,
        "patient_summary_after_tech_charge": summary_after_tech_charge,
        "patient_summary_after_all_charge": summary_after_all_charge,
        "medical_tech_tasks_checked": len(tasks),
        "drug_inventory_verified": {field: drug_row.get(field) for field in required_drug_fields},
        "drug_inventory_admin_verified": {field: admin_drug_row.get(field) for field in required_drug_fields},
        "drug_stock_trace": {
            "after_stock_check": checked_drugstore_row.get("stockNum"),
            "after_dispense": after_dispense_row.get("stockNum"),
            "after_refund": after_refund_row.get("stockNum"),
            "database_final": db_stock(seed["drug_id"]),
        },
        "stock_record_types": sorted({row.get("recordType") for row in stock_records}),
        "database_stock_record_types": sorted({row.get("record_type") for row in db_stock_movements}),
        "finance_record_types": sorted({row.get("recordType") for row in related_finance}),
        "database_finance_record_types": sorted({row.get("record_type") for row in db_related_finance}),
        "daily_finance_summary": daily,
        "final_patient_record": final_record,
        "headct": {
            "analysis_id": headct["analysis"]["analysisId"],
            "positive_probability": headct["analysis"].get("positiveProbability"),
            "report_service_id": headct["report_service_id"],
            "emr_document_id": headct["emr_document_id"],
            "persisted_ai": headct["persisted_ai"],
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
