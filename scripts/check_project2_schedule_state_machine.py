"""Exercise schedule-source state machine via real Project2 APIs."""

from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project2_db_env import get_project2_db_dsn  # noqa: E402


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


def context() -> dict[str, Any]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, deptment_id, regist_level_id FROM employee WHERE realname='doctor' AND role_type='DOCTOR' ORDER BY id LIMIT 1")
            doctor = cur.fetchone()
            cur.execute("SELECT id, real_name, gender, card_number, birthdate, phone, home_address FROM patient WHERE phone='13800001111' ORDER BY id DESC LIMIT 1")
            patient = cur.fetchone()
            cur.execute("SELECT id FROM settle_category WHERE delmark = TRUE ORDER BY id LIMIT 1")
            settle = cur.fetchone()
    assert_true(doctor is not None, "demo doctor missing")
    assert_true(patient is not None, "demo patient missing")
    assert_true(settle is not None, "settle category missing")
    return {
        "doctorId": int(doctor["id"]),
        "deptId": int(doctor["deptment_id"]),
        "registLevelId": int(doctor["regist_level_id"]),
        "settleCategoryId": int(settle["id"]),
        "patient": dict(patient),
    }


def choose_date(ctx: dict[str, Any]) -> str:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for offset in range(31, 90):
                candidate = date.today() + timedelta(days=offset)
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM register
                    WHERE patient_id = %s
                      AND employee_id = %s
                      AND visit_date = %s
                      AND visit_state IN ('REGISTERED','CHECKED_IN','DOCTOR_RECEIVED','ONGOING','CONSULTING')
                    """,
                    (ctx["patient"]["id"], ctx["doctorId"], candidate),
                )
                if int(cur.fetchone()["n"]) == 0:
                    return candidate.isoformat()
    raise RuntimeError("no free schedule test date")


def normal_schedule_count(ctx: dict[str, Any], visit_date: str, noon: str) -> dict[str, Any]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS n, array_agg(id ORDER BY id) AS ids, MAX(regist_quota) AS quota
                FROM scheduling
                WHERE employee_id = %s
                  AND deptment_id = %s
                  AND schedule_date = %s
                  AND noon = %s
                  AND schedule_status = 'NORMAL'
                """,
                (ctx["doctorId"], ctx["deptId"], visit_date, noon),
            )
            return dict(cur.fetchone())


def cleanup(register_id: int | None, schedule_ids: list[int]) -> None:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            if register_id:
                cur.execute("UPDATE register SET visit_state='CANCELLED', update_time=NOW() WHERE id=%s", (register_id,))
            if schedule_ids:
                cur.execute("UPDATE scheduling SET schedule_status='SUSPENDED', update_time=NOW() WHERE id=ANY(%s)", (schedule_ids,))
        conn.commit()


def main() -> None:
    ctx = context()
    visit_date = choose_date(ctx)
    noon = "AM"
    schedule_ids: list[int] = []
    register_id: int | None = None
    with httpx.Client(timeout=30.0) as client:
        try:
            unwrap(client.get(f"{PROJECT2}/actuator/health"))
            payload = {
                "doctorId": ctx["doctorId"],
                "deptId": ctx["deptId"],
                "scheduleDate": visit_date,
                "noon": noon,
                "registQuota": 5,
                "sourceType": "STATE_MACHINE_TEST",
            }
            first_id = int(unwrap(client.post(f"{PROJECT2}/api/schedule/sources", json=payload)))
            second_id = int(unwrap(client.post(f"{PROJECT2}/api/schedule/sources", json={**payload, "registQuota": 8})))
            schedule_ids = [first_id, second_id]
            after_duplicate = normal_schedule_count(ctx, visit_date, noon)
            assert_true(after_duplicate["n"] == 1, "重复创建号源后 NORMAL 排班必须只有一条", after_duplicate)
            assert_true(first_id == second_id, "重复创建同槽位号源应返回同一条 scheduleId", {"firstId": first_id, "secondId": second_id})
            assert_true(int(after_duplicate["quota"]) == 8, "重复创建应更新同一条号源配额", after_duplicate)

            patient = ctx["patient"]
            register_id = int(unwrap(client.post(
                f"{PROJECT2}/api/patient/register",
                json={
                    "realName": patient["real_name"],
                    "gender": patient["gender"],
                    "cardNumber": patient["card_number"],
                    "birthdate": str(patient["birthdate"]),
                    "homeAddress": patient["home_address"],
                    "phone": patient["phone"],
                    "deptId": ctx["deptId"],
                    "doctorId": ctx["doctorId"],
                    "visitDate": visit_date,
                    "noon": noon,
                    "registLevelId": ctx["registLevelId"],
                    "settleCategoryId": ctx["settleCategoryId"],
                    "registMethod": "APP",
                },
            )))

            low_quota = client.put(f"{PROJECT2}/api/schedule/sources/{first_id}/quota", json={"registQuota": 0})
            assert_true(low_quota.status_code >= 400, "号源配额不能被更新为 0", {"status": low_quota.status_code, "body": low_quota.text})
            below_used = client.put(f"{PROJECT2}/api/schedule/sources/{first_id}/quota", json={"registQuota": 1})
            assert_true(below_used.status_code < 400, "已有 1 个预约时配额 1 应允许", {"status": below_used.status_code, "body": below_used.text})

            print(json.dumps({
                "status": "PASS",
                "visitDate": visit_date,
                "scheduleId": first_id,
                "registerId": register_id,
                "normalScheduleCount": after_duplicate,
                "zeroQuotaRejectedStatus": low_quota.status_code,
            }, ensure_ascii=False, indent=2, default=str))
        finally:
            cleanup(register_id, schedule_ids)


if __name__ == "__main__":
    main()
