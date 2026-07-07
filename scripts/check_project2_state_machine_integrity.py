"""Validate Project2 queue state-machine invariants for demo accounts.

This script intentionally uses the real demo accounts and public Project2 APIs:
- admin creates doctor schedule sources
- patient registers to doctor
- doctor receives the patient

It verifies that one patient cannot be active multiple times in one doctor's
same-day queue and that receiving a patient moves the same register out of the
waiting queue.
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


def load_demo_context() -> dict[str, Any]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, deptment_id, regist_level_id
                FROM employee
                WHERE realname = 'doctor' AND role_type = 'DOCTOR'
                ORDER BY id LIMIT 1
                """
            )
            doctor = cur.fetchone()
            cur.execute(
                """
                SELECT id, real_name, gender, card_number, birthdate, phone, home_address
                FROM patient
                WHERE phone = '13800001111'
                ORDER BY id DESC LIMIT 1
                """
            )
            patient = cur.fetchone()
            cur.execute("SELECT id FROM settle_category WHERE delmark = TRUE ORDER BY id LIMIT 1")
            settle = cur.fetchone()
    assert_true(doctor is not None, "demo doctor missing")
    assert_true(patient is not None, "demo patient missing")
    assert_true(settle is not None, "settle category missing")
    return {
        "doctor_id": int(doctor["id"]),
        "dept_id": int(doctor["deptment_id"]),
        "regist_level_id": int(doctor["regist_level_id"]),
        "settle_category_id": int(settle["id"]),
        "patient": dict(patient),
    }


def cleanup(register_ids: list[int], schedule_ids: list[int], ctx: dict[str, Any] | None = None, visit_date: str | None = None) -> None:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            if register_ids:
                cur.execute("UPDATE register SET visit_state = 'CANCELLED' WHERE id = ANY(%s)", (register_ids,))
            if ctx and visit_date:
                cur.execute(
                    """
                    UPDATE register
                    SET visit_state = 'CANCELLED'
                    WHERE patient_id = %s
                      AND employee_id = %s
                      AND visit_date = %s
                      AND visit_state IN ('REGISTERED', 'CHECKED_IN', 'DOCTOR_RECEIVED', 'ONGOING', 'CONSULTING')
                    """,
                    (ctx["patient"]["id"], ctx["doctor_id"], visit_date),
                )
            if schedule_ids:
                cur.execute("DELETE FROM scheduling WHERE id = ANY(%s)", (schedule_ids,))
        conn.commit()


def choose_free_visit_date(ctx: dict[str, Any]) -> str:
    today = date.today()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for offset in range(7, 45):
                candidate = today + timedelta(days=offset)
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM register
                    WHERE patient_id = %s
                      AND employee_id = %s
                      AND visit_date = %s
                      AND visit_state IN ('REGISTERED', 'CHECKED_IN', 'DOCTOR_RECEIVED', 'ONGOING', 'CONSULTING')
                    """,
                    (ctx["patient"]["id"], ctx["doctor_id"], candidate),
                )
                if int(cur.fetchone()["n"]) == 0:
                    return candidate.isoformat()
    raise RuntimeError("no free future visit date for state-machine test")


def create_schedule(client: httpx.Client, ctx: dict[str, Any], visit_date: str, noon: str) -> int:
    payload = unwrap(
        client.post(
            f"{PROJECT2}/api/schedule/sources",
            json={
                "deptId": ctx["dept_id"],
                "doctorId": ctx["doctor_id"],
                "scheduleDate": visit_date,
                "noon": noon,
                "registQuota": 30,
                "registLevelId": ctx["regist_level_id"],
                "active": True,
            },
        )
    )
    if isinstance(payload, dict):
        return int(payload.get("scheduleId") or payload.get("id"))
    return int(payload)


def register_patient(client: httpx.Client, ctx: dict[str, Any], visit_date: str, noon: str) -> httpx.Response:
    patient = ctx["patient"]
    return client.post(
        f"{PROJECT2}/api/patient/register",
        json={
            "realName": patient["real_name"],
            "gender": patient["gender"],
            "cardNumber": patient["card_number"],
            "birthdate": str(patient["birthdate"]),
            "homeAddress": patient["home_address"],
            "phone": patient["phone"],
            "deptId": ctx["dept_id"],
            "doctorId": ctx["doctor_id"],
            "visitDate": visit_date,
            "noon": noon,
            "registLevelId": ctx["regist_level_id"],
            "settleCategoryId": ctx["settle_category_id"],
            "registMethod": "MOBILE",
        },
    )


def doctor_queue(client: httpx.Client, doctor_id: int, visit_state: str, visit_date: str, noon: str) -> list[dict[str, Any]]:
    page = unwrap(
        client.get(
            f"{PROJECT2}/api/doctor/patients",
            params={
                "doctorId": doctor_id,
                "visitState": visit_state,
                "visitDate": visit_date,
                "noon": noon,
                "pageNum": 1,
                "pageSize": 50,
            },
        )
    )
    return list(page.get("records") or [])


def main() -> None:
    ctx = load_demo_context()
    visit_date = choose_free_visit_date(ctx)
    register_ids: list[int] = []
    schedule_ids: list[int] = []
    with httpx.Client(timeout=30.0) as client:
        try:
            unwrap(client.get(f"{PROJECT2}/actuator/health"))
            schedule_ids.append(create_schedule(client, ctx, visit_date, "AM"))
            schedule_ids.append(create_schedule(client, ctx, visit_date, "PM"))

            first = register_patient(client, ctx, visit_date, "AM")
            first_id = int(unwrap(first))
            register_ids.append(first_id)

            duplicate = register_patient(client, ctx, visit_date, "PM")
            assert_true(
                duplicate.status_code >= 400,
                "同一患者同一医生同日第二个活跃挂号不应成功",
                {"status": duplicate.status_code, "body": duplicate.text, "firstRegisterId": first_id},
            )

            unwrap(client.put(f"{PROJECT2}/api/doctor/patients/{first_id}/receive"))
            waiting = doctor_queue(client, ctx["doctor_id"], "REGISTERED", visit_date, "AM")
            consulting = doctor_queue(client, ctx["doctor_id"], "DOCTOR_RECEIVED", visit_date, "AM")
            assert_true(first_id not in {row.get("registerId") for row in waiting}, "已接诊记录仍出现在待诊队列", waiting)
            assert_true(first_id in {row.get("registerId") for row in consulting}, "已接诊记录未出现在就诊中队列", consulting)

            print(json.dumps({
                "status": "PASS",
                "visitDate": visit_date,
                "doctorId": ctx["doctor_id"],
                "patientId": ctx["patient"]["id"],
                "firstRegisterId": first_id,
                "duplicateRejectedStatus": duplicate.status_code,
            }, ensure_ascii=False, indent=2))
        finally:
            cleanup(register_ids, schedule_ids, ctx, visit_date)


if __name__ == "__main__":
    main()
