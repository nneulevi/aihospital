"""Validate Project2 API fields that are rendered by the frontend.

This catches regressions where an endpoint exists and returns HTTP 200, but
important display fields are missing, raw status codes leak into user-facing
views, or generated response bodies are structurally empty.
"""

from __future__ import annotations

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


def payload(response: httpx.Response) -> Any:
    response.raise_for_status()
    body = response.json()
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def records(page: Any) -> list[dict[str, Any]]:
    if isinstance(page, dict):
        value = page.get("records")
        if isinstance(value, list):
            return value
    return []


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def non_empty(row: dict[str, Any], *fields: str) -> None:
    missing = [field for field in fields if row.get(field) in (None, "")]
    require(not missing, f"missing fields {missing} in {row}")


def first_row(conn: psycopg.Connection[Any], sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    require(row is not None, f"no sample row for query: {sql}")
    return dict(row)


def first_record(page: Any, name: str) -> dict[str, Any]:
    rows = records(page)
    require(bool(rows), f"{name} returned no records")
    return rows[0]


def assert_inventory(client: httpx.Client) -> None:
    admin_page = payload(client.get("/api/admin/drug/inventory", params={"pageNum": 1, "pageSize": 50}))
    admin_drug = next(
        (
            row
            for row in records(admin_page)
            if all(row.get(field) not in (None, "") for field in ("drugId", "drugCode", "drugName", "drugFormat", "drugUnit", "drugPrice", "manufacturer"))
        ),
        None,
    )
    require(admin_drug is not None, "admin drug inventory has no fully populated drug row")

    drugstore_page = payload(client.get("/api/drugstore/inventory", params={"pageNum": 1, "pageSize": 50}))
    drugstore_drug = first_record(drugstore_page, "drugstore inventory")
    non_empty(drugstore_drug, "drugId", "drugCode", "drugName", "drugFormat", "drugUnit", "stockNum", "drugPrice", "manufacturer")


def assert_patient_and_doctor(client: httpx.Client, conn: psycopg.Connection[Any]) -> None:
    schedule = first_row(
        conn,
        """
        SELECT s.deptment_id, s.schedule_date,
               CASE WHEN s.noon IN ('AM', 'MORNING') THEN 'MORNING' ELSE 'AFTERNOON' END AS noon
        FROM scheduling s
        JOIN employee e ON e.id = s.employee_id
        WHERE s.schedule_date >= CURRENT_DATE
          AND s.schedule_status = 'NORMAL'
          AND e.delmark = TRUE
          AND e.realname NOT LIKE '%%E2E%%'
          AND e.realname NOT LIKE '%%User Logic%%'
          AND e.realname NOT LIKE '%%Extended%%'
          AND e.realname NOT LIKE '%%项目验收%%'
          AND e.realname NOT LIKE '%%验收%%'
          AND e.realname NOT LIKE '%%测试%%'
        ORDER BY s.schedule_date, s.id
        LIMIT 1
        """,
    )
    doctors_page = payload(
        client.get(
            "/api/patient/doctors",
            params={
                "deptId": schedule["deptment_id"],
                "visitDate": schedule["schedule_date"].isoformat(),
                "noon": schedule["noon"],
                "pageNum": 1,
                "pageSize": 20,
            },
        )
    )
    doctor = first_record(doctors_page, "patient doctors")
    non_empty(doctor, "doctorId", "doctorName", "titleLevel", "scheduleDate", "noon", "registQuota", "remainingQuota")
    require(int(doctor["remainingQuota"]) <= int(doctor["registQuota"]), "remainingQuota exceeds registQuota")

    patient = first_row(
        conn,
        """
        SELECT patient_id
        FROM register
        ORDER BY update_time DESC NULLS LAST, id DESC
        LIMIT 1
        """,
    )
    patient_records = payload(
        client.get(
            "/api/patient/records",
            params={"patientId": patient["patient_id"], "pageNum": 1, "pageSize": 10},
        )
    )
    record = first_record(patient_records, "patient records")
    non_empty(record, "registerId", "visitDate", "deptName", "doctorName", "visitState", "visitStateName")
    require(record["visitStateName"] != record["visitState"], "patient record exposes raw visitState")

    detail = payload(client.get(f"/api/patient/records/{record['registerId']}"))
    non_empty(detail, "registerId", "visitDate", "deptName", "doctorName", "visitState", "visitStateName")
    require(detail["visitStateName"] != detail["visitState"], "patient record detail exposes raw visitState")

    doctor_detail = payload(client.get(f"/api/doctor/patients/{record['registerId']}"))
    non_empty(doctor_detail, "registerId", "caseNumber", "patientName", "gender", "registrationTime", "noon", "visitState")


def assert_workbench_lists(client: httpx.Client) -> None:
    finance_page = payload(client.get("/api/admin/finance/records", params={"pageNum": 1, "pageSize": 10}))
    if records(finance_page):
        finance = first_record(finance_page, "finance records")
        non_empty(finance, "id", "recordNo", "registerId", "patientName", "itemId", "itemType", "itemName", "amount", "recordType", "createTime")

    stock_page = payload(client.get("/api/drugstore/stock/records", params={"pageNum": 1, "pageSize": 10}))
    if records(stock_page):
        stock = first_record(stock_page, "drug stock records")
        non_empty(stock, "id", "drugId", "drugName", "recordType", "quantity", "beforeStock", "afterStock", "createTime")

    tech_page = payload(client.get("/api/medical-tech/tasks", params={"pageNum": 1, "pageSize": 10}))
    if records(tech_page):
        task = first_record(tech_page, "medical-tech tasks")
        non_empty(task, "itemType", "itemId", "registerId", "patientName", "projectName", "state", "price", "creationTime")

    source_page = payload(client.get("/api/schedule/sources", params={"pageNum": 1, "pageSize": 10}))
    source = first_record(source_page, "schedule sources")
    non_empty(source, "scheduleId", "doctorId", "doctorName", "deptId", "deptName", "scheduleDate", "noon", "registQuota", "scheduleStatus", "sourceType")


def assert_ai_schedule(client: httpx.Client, conn: psycopg.Connection[Any]) -> None:
    dept = first_row(
        conn,
        """
        SELECT deptment_id
        FROM employee
        WHERE role_type = 'DOCTOR'
          AND delmark = TRUE
          AND realname = 'doctor'
        ORDER BY id
        LIMIT 1
        """,
    )
    target = date.today() + timedelta(days=21)
    result = payload(
        client.post(
            "/api/ai/schedule/generate",
            json={
                "deptId": dept["deptment_id"],
                "startDate": target.isoformat(),
                "endDate": target.isoformat(),
                "ruleConfig": "field-consistency-check",
            },
        )
    )
    days = result.get("results") if isinstance(result, dict) else None
    require(isinstance(days, list) and days, "ai schedule generate returned empty results")
    day = days[0]
    require(day.get("date"), "ai schedule day lacks date")
    shifts = list(day.get("morning") or []) + list(day.get("afternoon") or [])
    require(bool(shifts), "ai schedule day lacks shifts")
    non_empty(shifts[0], "employeeId", "employeeName", "quota", "shiftType")


def main() -> None:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with httpx.Client(base_url=PROJECT2, timeout=30.0) as client:
            payload(client.get("/actuator/health"))
            assert_inventory(client)
            assert_patient_and_doctor(client, conn)
            assert_workbench_lists(client)
            assert_ai_schedule(client, conn)
    print("Project2 field consistency check passed")


if __name__ == "__main__":
    main()
