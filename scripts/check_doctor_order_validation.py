"""Validate doctor-side order forms reject empty business fields.

The test creates one temporary real demo-account visit, receives it as doctor,
then verifies that CHECK/INSPECTION/DISPOSAL requests with blank names or
positions are rejected and do not create rows.
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

from project2_db_env import get_project2_db_dsn


ROOT = Path(__file__).resolve().parents[1]
PROJECT2 = os.getenv("PROJECT2_BASE_URL", "http://127.0.0.1:8092")
DB_DSN = get_project2_db_dsn(ROOT)


def unwrap(response: httpx.Response) -> Any:
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code} {response.request.method} {response.request.url}: {response.text}")
    if not response.text.strip():
        return None
    return response.json()


def assert_true(condition: bool, message: str, payload: Any = None) -> None:
    if not condition:
        suffix = "" if payload is None else "\n" + json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        raise RuntimeError(message + suffix)


def load_context() -> dict[str, Any]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, deptment_id, regist_level_id FROM employee WHERE realname = 'doctor' AND role_type = 'DOCTOR' ORDER BY id LIMIT 1")
            doctor = cur.fetchone()
            cur.execute("SELECT id, real_name, gender, card_number, birthdate, phone, home_address FROM patient WHERE phone = '13800001111' ORDER BY id DESC LIMIT 1")
            patient = cur.fetchone()
            cur.execute("SELECT id FROM settle_category WHERE delmark = TRUE ORDER BY id LIMIT 1")
            settle = cur.fetchone()
            cur.execute("SELECT id FROM medical_technology WHERE tech_code = 'BIZ-CT-HEAD' AND tech_type = 'CHECK' ORDER BY id LIMIT 1")
            check = cur.fetchone()
            cur.execute("SELECT id FROM medical_technology WHERE tech_code = 'BIZ-BLOOD-ROUTINE' AND tech_type = 'INSPECTION' ORDER BY id LIMIT 1")
            inspection = cur.fetchone()
            cur.execute("SELECT id FROM medical_technology WHERE tech_type = 'DISPOSAL' AND tech_name = '清创换药' ORDER BY id LIMIT 1")
            disposal = cur.fetchone()
    for name, value in {
        "doctor": doctor,
        "patient": patient,
        "settle": settle,
        "check": check,
        "inspection": inspection,
        "disposal": disposal,
    }.items():
        assert_true(value is not None, f"{name} seed data missing")
    return {
        "doctor_id": int(doctor["id"]),
        "dept_id": int(doctor["deptment_id"]),
        "regist_level_id": int(doctor["regist_level_id"]),
        "settle_category_id": int(settle["id"]),
        "patient": dict(patient),
        "check_id": int(check["id"]),
        "inspection_id": int(inspection["id"]),
        "disposal_id": int(disposal["id"]),
    }


def cleanup(register_ids: list[int], schedule_ids: list[int]) -> None:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            if register_ids:
                cur.execute("DELETE FROM check_request WHERE register_id = ANY(%s)", (register_ids,))
                cur.execute("DELETE FROM inspection_request WHERE register_id = ANY(%s)", (register_ids,))
                cur.execute("DELETE FROM disposal_request WHERE register_id = ANY(%s)", (register_ids,))
                cur.execute("DELETE FROM medical_record WHERE register_id = ANY(%s)", (register_ids,))
                cur.execute("UPDATE register SET visit_state = 'CANCELLED' WHERE id = ANY(%s)", (register_ids,))
            if schedule_ids:
                cur.execute("DELETE FROM scheduling WHERE id = ANY(%s)", (schedule_ids,))
        conn.commit()


def create_schedule(client: httpx.Client, ctx: dict[str, Any], visit_date: str) -> int:
    payload = unwrap(client.post(f"{PROJECT2}/api/schedule/sources", json={
        "deptId": ctx["dept_id"],
        "doctorId": ctx["doctor_id"],
        "scheduleDate": visit_date,
        "noon": "AM",
        "registQuota": 30,
        "registLevelId": ctx["regist_level_id"],
        "active": True,
    }))
    if isinstance(payload, dict):
        return int(payload.get("scheduleId") or payload.get("id"))
    return int(payload)


def create_visit(client: httpx.Client, ctx: dict[str, Any], visit_date: str) -> int:
    patient = ctx["patient"]
    register_id = int(unwrap(client.post(f"{PROJECT2}/api/patient/register", json={
        "realName": patient["real_name"],
        "gender": patient["gender"],
        "cardNumber": patient["card_number"],
        "birthdate": str(patient["birthdate"]),
        "homeAddress": patient["home_address"],
        "phone": patient["phone"],
        "deptId": ctx["dept_id"],
        "doctorId": ctx["doctor_id"],
        "visitDate": visit_date,
        "noon": "AM",
        "registLevelId": ctx["regist_level_id"],
        "settleCategoryId": ctx["settle_category_id"],
        "registMethod": "MOBILE",
    })))
    unwrap(client.put(f"{PROJECT2}/api/doctor/patients/{register_id}/receive"))
    return register_id


def row_counts(register_id: int) -> dict[str, int]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            result = {}
            for table in ["check_request", "inspection_request", "disposal_request"]:
                cur.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE register_id = %s", (register_id,))
                result[table] = int(cur.fetchone()["n"])
            return result


def assert_rejected(response: httpx.Response, label: str) -> None:
    assert_true(response.status_code >= 400, f"{label} 空字段提交不应成功", {
        "status": response.status_code,
        "body": response.text,
    })


def main() -> None:
    ctx = load_context()
    visit_date = (date.today() + timedelta(days=6)).isoformat()
    register_ids: list[int] = []
    schedule_ids: list[int] = []
    with httpx.Client(timeout=30.0) as client:
        try:
            unwrap(client.get(f"{PROJECT2}/actuator/health"))
            schedule_ids.append(create_schedule(client, ctx, visit_date))
            register_id = create_visit(client, ctx, visit_date)
            register_ids.append(register_id)
            before = row_counts(register_id)

            assert_rejected(client.post(f"{PROJECT2}/api/doctor/check-request", json={
                "registerId": register_id,
                "items": [{"medicalTechnologyId": ctx["check_id"], "checkInfo": "", "checkPosition": ""}],
            }), "检查")
            assert_rejected(client.post(f"{PROJECT2}/api/doctor/inspection-request", json={
                "registerId": register_id,
                "items": [{"medicalTechnologyId": ctx["inspection_id"], "inspectionInfo": "", "inspectionPosition": ""}],
            }), "检验")
            assert_rejected(client.post(f"{PROJECT2}/api/doctor/disposal-request", json={
                "registerId": register_id,
                "items": [{"medicalTechnologyId": ctx["disposal_id"], "disposalInfo": "", "disposalPosition": ""}],
            }), "处置")

            after = row_counts(register_id)
            assert_true(before == after, "空字段提交不应产生检查/检验/处置记录", {"before": before, "after": after})
            print(json.dumps({
                "status": "PASS",
                "registerId": register_id,
                "counts": after,
            }, ensure_ascii=False, indent=2))
        finally:
            cleanup(register_ids, schedule_ids)


if __name__ == "__main__":
    main()
