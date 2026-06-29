"""Run Project2 core HIS business workflow without the Head CT AI chain.

The workflow validates the main platform's own outpatient functionality:

1. Seed minimal master data: department, doctor, pharmacist, schedule, level,
   settlement category, medical technology, drug and disease.
2. Register a patient through Project2 API.
3. Doctor receives the patient through Project2 API.
4. Save medical record, create check/inspection/disposal requests and a prescription.
5. Charge, dispense, refund drugs and cancel an unused registration.
6. Verify persisted database state.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row


PROJECT2 = os.getenv("PROJECT2_BASE_URL", "http://127.0.0.1:8092")
DB_DSN = os.getenv("PROJECT2_DB_DSN", "postgresql://postgres:postgres@localhost:5432/hospital")


def require_ok(response: httpx.Response) -> Any:
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        return None
    return response.json()


REQUIRED_TABLES = [
    "department",
    "employee",
    "regist_level",
    "settle_category",
    "scheduling",
    "patient",
    "register",
    "medical_record",
    "medical_technology",
    "check_request",
    "inspection_request",
    "disposal_request",
    "drug_info",
    "prescription",
    "prescription_detail",
    "disease",
    "medical_record_disease",
    "ai_consultation",
    "ai_diagnosis_suggestion",
    "ai_image_file",
    "ai_image_analysis",
    "ai_generated_report",
    "ai_schedule_rule",
    "ai_schedule_result",
]


def assert_schema_ready(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = ANY(%s)
            """,
            (REQUIRED_TABLES,),
        )
        existing = {row["table_name"] for row in cur.fetchall()}
        missing = sorted(set(REQUIRED_TABLES) - existing)
        if missing:
            raise RuntimeError(
                "Project2 database schema is incomplete. Missing tables: "
                + ", ".join(missing)
                + ". Run: powershell -ExecutionPolicy Bypass -File Project2/sql/init_project2_db.ps1"
            )

        for table_name in [
            "department",
            "employee",
            "regist_level",
            "settle_category",
            "scheduling",
            "patient",
            "register",
            "medical_record",
            "medical_technology",
            "check_request",
            "inspection_request",
            "disposal_request",
            "drug_info",
            "prescription",
            "prescription_detail",
            "disease",
        ]:
            cur.execute("SELECT pg_get_serial_sequence(%s, 'id') AS seq", (table_name,))
            row = cur.fetchone()
            seq = row["seq"] if row else None
            if seq:
                cur.execute(f"SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false)", (seq,))
    conn.commit()

def seed_master_data() -> dict[str, Any]:
    suffix = uuid.uuid4().hex[:8]
    today = date.today()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        assert_schema_ready(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO department(dept_code, dept_name, dept_type, delmark)
                VALUES (%s, '神经外科', 'CLINICAL', TRUE)
                RETURNING id
                """,
                (f"DEPT-{suffix}",),
            )
            dept_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO regist_level(regist_code, regist_name, regist_fee, regist_quota, is_expert, sequence_no, delmark)
                VALUES (%s, '普通号', 20.00, 50, FALSE, 1, TRUE)
                RETURNING id
                """,
                (f"RL-{suffix}",),
            )
            regist_level_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO settle_category(settle_code, settle_name, sequence_no, delmark)
                VALUES (%s, '自费', 1, TRUE)
                RETURNING id
                """,
                (f"SC-{suffix}",),
            )
            settle_category_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO employee(deptment_id, regist_level_id, realname, role_type, title_level, password_hash, phone, delmark)
                VALUES (%s, %s, 'E2E医生', 'DOCTOR', '主治医师', 'e2e', '13800000001', TRUE)
                RETURNING id
                """,
                (dept_id, regist_level_id),
            )
            doctor_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark)
                VALUES (%s, 'E2E药师', 'PHARMACIST', '药师', 'e2e', '13800000002', TRUE)
                RETURNING id
                """,
                (dept_id,),
            )
            pharmacist_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO scheduling(employee_id, deptment_id, schedule_date, noon, regist_quota, schedule_status, source_type)
                VALUES (%s, %s, %s, 'AM', 50, 'NORMAL', 'MANUAL')
                RETURNING id
                """,
                (doctor_id, dept_id, today),
            )
            schedule_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO medical_technology(tech_code, tech_name, tech_format, tech_price, tech_type, price_type, deptment_id)
                VALUES (%s, '头颅CT平扫', '次', 180.00, 'CHECK', '检查费', %s)
                RETURNING id
                """,
                (f"CT-{suffix}", dept_id),
            )
            check_tech_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO medical_technology(tech_code, tech_name, tech_format, tech_price, tech_type, price_type, deptment_id)
                VALUES (%s, '血常规', '次', 25.00, 'INSPECTION', '检验费', %s)
                RETURNING id
                """,
                (f"LAB-{suffix}", dept_id),
            )
            inspection_tech_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO medical_technology(tech_code, tech_name, tech_format, tech_price, tech_type, price_type, deptment_id)
                VALUES (%s, '清创换药', '次', 35.00, 'DISPOSAL', '处置费', %s)
                RETURNING id
                """,
                (f"DISP-{suffix}", dept_id),
            )
            disposal_tech_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO drug_info(drug_code, drug_name, drug_format, drug_unit, stock_num, drug_price, manufacturer, drug_type)
                VALUES (%s, '布洛芬缓释胶囊', '0.3g*20粒', '盒', 100, 18.50, 'E2E药厂', '西药')
                RETURNING id
                """,
                (f"DRUG-{suffix}",),
            )
            drug_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO disease(disease_code, disease_name, disease_type, icd_code)
                VALUES (%s, '头部外伤后观察', '外科', 'S09.900')
                RETURNING id
                """,
                (f"DIS-{suffix}",),
            )
            disease_id = int(cur.fetchone()["id"])
        conn.commit()
    return {
        "suffix": suffix,
        "visit_date": today.isoformat(),
        "dept_id": dept_id,
        "doctor_id": doctor_id,
        "pharmacist_id": pharmacist_id,
        "regist_level_id": regist_level_id,
        "settle_category_id": settle_category_id,
        "schedule_id": schedule_id,
        "check_tech_id": check_tech_id,
        "inspection_tech_id": inspection_tech_id,
        "disposal_tech_id": disposal_tech_id,
        "drug_id": drug_id,
        "disease_id": disease_id,
        "drug_unit_price": Decimal("18.50"),
    }


def fetch_db_summary(register_id: int, prescription_id: int, drug_id: int) -> dict[str, Any]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT patient_id, visit_state FROM register WHERE id = %s", (register_id,))
            register = dict(cur.fetchone())
            cur.execute("SELECT COUNT(*) AS n FROM medical_record WHERE register_id = %s", (register_id,))
            medical_record_count = int(cur.fetchone()["n"])
            cur.execute("SELECT COUNT(*) AS n FROM check_request WHERE register_id = %s", (register_id,))
            check_count = int(cur.fetchone()["n"])
            cur.execute("SELECT COUNT(*) AS n FROM inspection_request WHERE register_id = %s", (register_id,))
            inspection_count = int(cur.fetchone()["n"])
            cur.execute("SELECT COUNT(*) AS n FROM disposal_request WHERE register_id = %s", (register_id,))
            disposal_count = int(cur.fetchone()["n"])
            cur.execute("SELECT prescription_status, total_amount FROM prescription WHERE id = %s", (prescription_id,))
            prescription = dict(cur.fetchone())
            cur.execute("SELECT stock_num FROM drug_info WHERE id = %s", (drug_id,))
            stock = int(cur.fetchone()["stock_num"])
    return {
        "register": register,
        "medical_record_count": medical_record_count,
        "check_count": check_count,
        "inspection_count": inspection_count,
        "disposal_count": disposal_count,
        "prescription": prescription,
        "drug_stock": stock,
    }


def main() -> None:
    seed = seed_master_data()
    numeric_suffix = str(int(seed["suffix"], 16) % 100000).zfill(5)
    card_number = "110101197001" + numeric_suffix + "X"
    drug_number = 2
    charge_amount = str(seed["drug_unit_price"] * drug_number)

    with httpx.Client(timeout=60) as client:
        health = require_ok(client.get(f"{PROJECT2}/actuator/health"))
        doctors = require_ok(
            client.get(
                f"{PROJECT2}/api/patient/doctors",
                params={
                    "deptId": seed["dept_id"],
                    "visitDate": seed["visit_date"],
                    "noon": "AM",
                    "pageNum": 1,
                    "pageSize": 10,
                },
            )
        )
        register_id = require_ok(
            client.post(
                f"{PROJECT2}/api/patient/register",
                json={
                    "realName": "Project2独立验收患者",
                    "gender": "M",
                    "cardNumber": card_number,
                    "birthdate": "1970-01-01",
                    "homeAddress": "Project2 E2E",
                    "phone": "13800001111",
                    "deptId": seed["dept_id"],
                    "doctorId": seed["doctor_id"],
                    "visitDate": seed["visit_date"],
                    "noon": "AM",
                    "registLevelId": seed["regist_level_id"],
                    "settleCategoryId": seed["settle_category_id"],
                    "registMethod": "WINDOW",
                },
            )
        )
        waiting_patients = require_ok(
            client.get(
                f"{PROJECT2}/api/doctor/patients",
                params={"doctorId": seed["doctor_id"], "visitState": "REGISTERED", "pageNum": 1, "pageSize": 10},
            )
        )
        require_ok(client.put(f"{PROJECT2}/api/doctor/patients/{register_id}/receive"))
        require_ok(
            client.post(
                f"{PROJECT2}/api/doctor/medical-record",
                json={
                    "registerId": register_id,
                    "readme": "头部外伤后头痛头晕",
                    "present": "头痛、头晕、恶心，需观察颅脑损伤风险。",
                    "history": "既往体健。",
                    "allergy": "无",
                    "physique": "神志清楚，生命体征平稳。",
                    "proposal": "完善头颅CT、血常规，必要时随诊。",
                    "diagnosis": "头部外伤后观察",
                },
            )
        )
        require_ok(
            client.post(
                f"{PROJECT2}/api/doctor/check-request",
                json={
                    "registerId": register_id,
                    "items": [
                        {
                            "medicalTechnologyId": seed["check_tech_id"],
                            "checkInfo": "头颅CT平扫",
                            "checkPosition": "head",
                        }
                    ],
                },
            )
        )
        require_ok(
            client.post(
                f"{PROJECT2}/api/doctor/inspection-request",
                json={
                    "registerId": register_id,
                    "items": [
                        {
                            "medicalTechnologyId": seed["inspection_tech_id"],
                            "inspectionInfo": "血常规",
                            "inspectionPosition": "blood",
                        }
                    ],
                },
            )
        )
        require_ok(
            client.post(
                f"{PROJECT2}/api/doctor/disposal-request",
                json={
                    "registerId": register_id,
                    "items": [
                        {
                            "medicalTechnologyId": seed["disposal_tech_id"],
                            "disposalInfo": "清创换药",
                            "disposalPosition": "head wound",
                        }
                    ],
                },
            )
        )
        prescription_id = require_ok(
            client.post(
                f"{PROJECT2}/api/doctor/prescription",
                json={
                    "registerId": register_id,
                    "doctorId": seed["doctor_id"],
                    "items": [
                        {
                            "drugId": seed["drug_id"],
                            "usageRoute": "口服",
                            "frequency": "每日两次",
                            "dosage": "1粒",
                            "singleDose": "1粒",
                            "useDays": 3,
                            "drugNumber": drug_number,
                        }
                    ],
                },
            )
        )
        orders = require_ok(
            client.get(
                f"{PROJECT2}/api/patient/orders",
                params={"patientId": fetch_db_summary(register_id, prescription_id, seed["drug_id"])["register"]["patient_id"], "pageNum": 1, "pageSize": 20},
            )
        )
        require_ok(
            client.post(
                f"{PROJECT2}/api/admin/finance/charge",
                json={
                    "registerId": register_id,
                    "itemIds": [prescription_id],
                    "chargeMethod": "CASH",
                    "amount": charge_amount,
                },
            )
        )
        require_ok(
            client.post(
                f"{PROJECT2}/api/admin/drug/dispense",
                json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"]},
            )
        )
        require_ok(
            client.post(
                f"{PROJECT2}/api/admin/drug/refund",
                json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"], "refundReason": "验收退药"},
            )
        )
        require_ok(
            client.put(
                f"{PROJECT2}/api/doctor/diagnosis/confirm",
                json={
                    "registerId": register_id,
                    "diagnosis": "头部外伤后观察",
                    "cure": "门诊随访",
                    "diseaseIds": [seed["disease_id"]],
                },
            )
        )
        check_results = require_ok(client.get(f"{PROJECT2}/api/doctor/check-results/{register_id}"))
        admin_dashboard = require_ok(client.get(f"{PROJECT2}/api/admin/dashboard/summary"))
        doctor_dashboard = require_ok(
            client.get(
                f"{PROJECT2}/api/doctor/dashboard/summary",
                params={"doctorId": seed["doctor_id"]},
            )
        )
        patient_dashboard = require_ok(
            client.get(
                f"{PROJECT2}/api/patient/dashboard/summary",
                params={"patientId": fetch_db_summary(register_id, prescription_id, seed["drug_id"])["register"]["patient_id"]},
            )
        )

        cancel_register_id = require_ok(
            client.post(
                f"{PROJECT2}/api/patient/register",
                json={
                    "realName": "Project2退号验收患者",
                    "gender": "F",
                    "cardNumber": "110101198002" + numeric_suffix + "X",
                    "birthdate": "1980-02-02",
                    "homeAddress": "Project2 E2E",
                    "phone": "13800002222",
                    "deptId": seed["dept_id"],
                    "doctorId": seed["doctor_id"],
                    "visitDate": seed["visit_date"],
                    "noon": "AM",
                    "registLevelId": seed["regist_level_id"],
                    "settleCategoryId": seed["settle_category_id"],
                    "registMethod": "WINDOW",
                },
            )
        )
        require_ok(
            client.put(
                f"{PROJECT2}/api/patient/register/cancel",
                json={"registerId": cancel_register_id, "cancelReason": "独立业务验收退号"},
            )
        )

    db_summary = fetch_db_summary(register_id, prescription_id, seed["drug_id"])
    if health.get("status") != "UP":
        raise RuntimeError(f"Project2 health is not UP: {health}")
    if not doctors.get("records"):
        raise RuntimeError("doctor list is empty")
    if not waiting_patients.get("records"):
        raise RuntimeError("registered patient was not visible in doctor queue")
    if db_summary["medical_record_count"] < 1:
        raise RuntimeError("medical record was not persisted")
    if db_summary["check_count"] < 1 or db_summary["inspection_count"] < 1 or db_summary["disposal_count"] < 1:
        raise RuntimeError(f"medical orders were not persisted: {db_summary}")
    if db_summary["prescription"]["prescription_status"] != "REFUNDED":
        raise RuntimeError(f"prescription final status is not REFUNDED: {db_summary['prescription']}")
    if db_summary["drug_stock"] != 100:
        raise RuntimeError(f"drug stock was not restored after refund: {db_summary['drug_stock']}")
    if admin_dashboard.get("todayRegistrations", 0) <= 0:
        raise RuntimeError(f"admin dashboard did not include today's registration: {admin_dashboard}")
    if doctor_dashboard.get("doctorId") != seed["doctor_id"]:
        raise RuntimeError(f"doctor dashboard was not scoped to seeded doctor: {doctor_dashboard}")
    if patient_dashboard.get("recordCount", 0) <= 0:
        raise RuntimeError(f"patient dashboard did not include patient records: {patient_dashboard}")

    summary = {
        "status": "success",
        "health": health.get("status"),
        "master_data": seed,
        "register_id": register_id,
        "cancel_register_id": cancel_register_id,
        "prescription_id": prescription_id,
        "doctor_list_count": len(doctors.get("records") or []),
        "waiting_patient_count": len(waiting_patients.get("records") or []),
        "orders_count": len(orders.get("records") or []),
        "check_result_sections": {
            "checks": len(check_results.get("checkRequests") or []),
            "inspections": len(check_results.get("inspectionRequests") or []),
            "disposals": len(check_results.get("disposalRequests") or []),
        },
        "dashboard": {
            "admin": admin_dashboard,
            "doctor": doctor_dashboard,
            "patient": patient_dashboard,
        },
        "db_summary": db_summary,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

