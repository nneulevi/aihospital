"""Validate Project2 medical-tech, drug inventory and schedule-source workflows."""

from __future__ import annotations

import json
import os
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
DB_DSN = get_project2_db_dsn(ROOT)


def unwrap(response: httpx.Response) -> Any:
    response.raise_for_status()
    if not response.text.strip():
        return None
    return response.json()


def require_tables(conn: psycopg.Connection[Any]) -> None:
    required = {
        "department", "employee", "regist_level", "settle_category", "scheduling",
        "patient", "register", "medical_technology", "check_request",
        "inspection_request", "disposal_request", "drug_info", "prescription",
        "prescription_detail", "drug_stock_record",
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


def seed_data() -> dict[str, Any]:
    suffix = uuid.uuid4().hex[:8]
    today = date.today()
    tomorrow = today + timedelta(days=1)
    drug_name = f"\u795e\u7ecf\u79d1\u7518\u9732\u9187\u6ce8\u5c04\u6db2-{suffix}"

    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        require_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO department(dept_code, dept_name, dept_type, delmark)
                VALUES (%s, %s, 'MEDICAL_TECH', TRUE)
                RETURNING id
                """,
                (f"EXT-DEPT-{suffix}", f"\u9879\u76ee\u9a8c\u6536\u795e\u7ecf\u5f71\u50cf\u79d1-{suffix}"),
            )
            dept_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO regist_level(regist_code, regist_name, regist_fee, regist_quota, is_expert, sequence_no, delmark)
                VALUES (%s, %s, 20.00, 50, FALSE, 1, TRUE)
                RETURNING id
                """,
                (f"EXT-RL-{suffix}", "\u9879\u76ee\u9a8c\u6536\u666e\u901a\u53f7"),
            )
            regist_level_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO settle_category(settle_code, settle_name, sequence_no, delmark)
                VALUES (%s, %s, 1, TRUE)
                RETURNING id
                """,
                (f"EXT-SC-{suffix}", "\u81ea\u8d39"),
            )
            settle_category_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO employee(deptment_id, regist_level_id, realname, role_type, title_level, password_hash, phone, delmark)
                VALUES (%s, %s, %s, 'DOCTOR', %s, 'e2e', '13900001001', TRUE)
                RETURNING id
                """,
                (dept_id, regist_level_id, "\u795e\u7ecf\u5f71\u50cf\u533b\u751f", "\u4e3b\u4efb\u533b\u5e08"),
            )
            doctor_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark)
                VALUES (%s, %s, 'MEDICAL_TECH', %s, 'e2e', '13900001002', TRUE)
                RETURNING id
                """,
                (dept_id, "\u5f71\u50cf\u6280\u5e08", "\u6280\u5e08"),
            )
            tech_employee_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark)
                VALUES (%s, %s, 'PHARMACIST', %s, 'e2e', '13900001003', TRUE)
                RETURNING id
                """,
                (dept_id, "\u95e8\u8bca\u836f\u5e08", "\u836f\u5e08"),
            )
            pharmacist_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO scheduling(employee_id, deptment_id, schedule_date, noon, regist_quota, schedule_status, source_type)
                VALUES (%s, %s, %s, 'AM', 30, 'NORMAL', 'MANUAL')
                RETURNING id
                """,
                (doctor_id, dept_id, today),
            )
            initial_schedule_id = int(cur.fetchone()["id"])

            tech_ids: dict[str, int] = {}
            for tech_type, name, price in [
                ("CHECK", "\u9879\u76ee\u9a8c\u6536\u5934\u9885CT", Decimal("180.00")),
                ("INSPECTION", "\u9879\u76ee\u9a8c\u6536\u8840\u5e38\u89c4", Decimal("25.00")),
                ("DISPOSAL", "\u9879\u76ee\u9a8c\u6536\u6e05\u521b\u6362\u836f", Decimal("35.00")),
            ]:
                cur.execute(
                    """
                    INSERT INTO medical_technology(tech_code, tech_name, tech_format, tech_price, tech_type, price_type, deptment_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (f"EXT-{tech_type}-{suffix}", name, "\u6b21", price, tech_type, "\u533b\u6280\u8d39", dept_id),
                )
                tech_ids[tech_type] = int(cur.fetchone()["id"])

            cur.execute(
                """
                INSERT INTO drug_info(drug_code, drug_name, drug_format, drug_unit, stock_num, drug_price, manufacturer, drug_type)
                VALUES (%s, %s, '250ml', %s, 8, 12.50, %s, %s)
                RETURNING id
                """,
                (f"NEURO-DRUG-{suffix}", drug_name, "\u74f6", "\u534e\u5317\u5236\u836f", "\u897f\u836f"),
            )
            drug_id = int(cur.fetchone()["id"])
        conn.commit()

    return {
        "suffix": suffix,
        "today": today.isoformat(),
        "tomorrow": tomorrow.isoformat(),
        "dept_id": dept_id,
        "doctor_id": doctor_id,
        "tech_employee_id": tech_employee_id,
        "pharmacist_id": pharmacist_id,
        "regist_level_id": regist_level_id,
        "settle_category_id": settle_category_id,
        "initial_schedule_id": initial_schedule_id,
        "check_tech_id": tech_ids["CHECK"],
        "inspection_tech_id": tech_ids["INSPECTION"],
        "disposal_tech_id": tech_ids["DISPOSAL"],
        "drug_id": drug_id,
        "drug_name": drug_name,
    }


def fetch_stock_and_records(drug_id: int) -> dict[str, Any]:
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stock_num FROM drug_info WHERE id = %s", (drug_id,))
            stock = int(cur.fetchone()["stock_num"])
            cur.execute(
                """
                SELECT record_type, quantity, before_stock, after_stock
                FROM drug_stock_record
                WHERE drug_id = %s
                ORDER BY id
                """,
                (drug_id,),
            )
            records = [dict(row) for row in cur.fetchall()]
    return {"stock": stock, "records": records}


def assert_inventory_row(row: dict[str, Any], seed: dict[str, Any]) -> None:
    required = {
        "drugId": seed["drug_id"],
        "drugName": seed["drug_name"],
        "drugFormat": "250ml",
        "drugUnit": "\u74f6",
        "manufacturer": "\u534e\u5317\u5236\u836f",
    }
    for key, expected in required.items():
        if row.get(key) != expected:
            raise RuntimeError(f"drug inventory field mismatch for {key}: expected={expected!r}, actual={row.get(key)!r}, row={row}")


def main() -> None:
    seed = seed_data()
    numeric_suffix = str(int(seed["suffix"], 16) % 100000).zfill(5)

    with httpx.Client(timeout=60) as client:
        health = unwrap(client.get(f"{PROJECT2}/actuator/health"))
        if health.get("status") != "UP":
            raise RuntimeError(f"Project2 health is not UP: {health}")

        schedule_id = unwrap(client.post(f"{PROJECT2}/api/schedule/sources", json={
            "doctorId": seed["doctor_id"],
            "deptId": seed["dept_id"],
            "scheduleDate": seed["tomorrow"],
            "noon": "PM",
            "registQuota": 12,
            "sourceType": "MANUAL",
        }))
        unwrap(client.put(f"{PROJECT2}/api/schedule/sources/{schedule_id}/quota", json={"registQuota": 18}))
        unwrap(client.put(f"{PROJECT2}/api/schedule/sources/{schedule_id}/suspend", json={"reason": "\u4e34\u65f6\u505c\u8bca\u6f14\u7ec3"}))
        unwrap(client.put(f"{PROJECT2}/api/schedule/sources/{schedule_id}/resume", json={"reason": "\u6062\u590d\u63a5\u8bca"}))
        sources = unwrap(client.get(f"{PROJECT2}/api/schedule/sources", params={"deptId": seed["dept_id"], "startDate": seed["tomorrow"], "endDate": seed["tomorrow"]}))
        if not any(item.get("scheduleId") == schedule_id and item.get("registQuota") == 18 for item in sources.get("records", [])):
            raise RuntimeError(f"created schedule source not visible or quota not updated: {sources}")

        register_id = unwrap(client.post(f"{PROJECT2}/api/patient/register", json={
            "realName": "\u9879\u76ee\u9a8c\u6536\u60a3\u8005",
            "gender": "M",
            "cardNumber": "110101197505" + numeric_suffix + "X",
            "birthdate": "1975-05-05",
            "homeAddress": "Project2 扩展业务场景",
            "phone": "13900001111",
            "deptId": seed["dept_id"],
            "doctorId": seed["doctor_id"],
            "visitDate": seed["today"],
            "noon": "AM",
            "registLevelId": seed["regist_level_id"],
            "settleCategoryId": seed["settle_category_id"],
            "registMethod": "WINDOW",
        }))
        unwrap(client.put(f"{PROJECT2}/api/doctor/patients/{register_id}/receive"))
        unwrap(client.post(f"{PROJECT2}/api/doctor/check-request", json={"registerId": register_id, "items": [{"medicalTechnologyId": seed["check_tech_id"], "checkInfo": "\u5934\u9885CT", "checkPosition": "head"}]}))
        unwrap(client.post(f"{PROJECT2}/api/doctor/inspection-request", json={"registerId": register_id, "items": [{"medicalTechnologyId": seed["inspection_tech_id"], "inspectionInfo": "\u8840\u5e38\u89c4", "inspectionPosition": "blood"}]}))
        unwrap(client.post(f"{PROJECT2}/api/doctor/disposal-request", json={"registerId": register_id, "items": [{"medicalTechnologyId": seed["disposal_tech_id"], "disposalInfo": "\u6e05\u521b\u6362\u836f", "disposalPosition": "head"}]}))

        with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM check_request WHERE register_id = %s ORDER BY id DESC LIMIT 1", (register_id,))
                check_id = int(cur.fetchone()["id"])
                cur.execute("SELECT id FROM inspection_request WHERE register_id = %s ORDER BY id DESC LIMIT 1", (register_id,))
                inspection_id = int(cur.fetchone()["id"])
                cur.execute("SELECT id FROM disposal_request WHERE register_id = %s ORDER BY id DESC LIMIT 1", (register_id,))
                disposal_id = int(cur.fetchone()["id"])

        unwrap(client.post(f"{PROJECT2}/api/admin/finance/charge", json={"registerId": register_id, "itemIds": [check_id, inspection_id, disposal_id], "itemTypes": ["CHECK", "INSPECTION", "DISPOSAL"], "chargeMethod": "CASH", "amount": "240.00"}))
        tasks = unwrap(client.get(f"{PROJECT2}/api/medical-tech/tasks", params={"registerId": register_id, "state": "CHARGED"}))
        if len(tasks.get("records", [])) < 3:
            raise RuntimeError(f"medical-tech charged tasks not visible: {tasks}")
        for item_type, item_id, result_text in [
            ("CHECK", check_id, "\u5934\u9885CT\u672a\u89c1\u660e\u663e\u6025\u6027\u51fa\u8840\u5f81\u8c61"),
            ("INSPECTION", inspection_id, "\u767d\u7ec6\u80de\u8ba1\u6570\u8f7b\u5ea6\u5347\u9ad8"),
            ("DISPOSAL", disposal_id, "\u4f24\u53e3\u6e05\u6d01\u6362\u836f\u5b8c\u6210"),
        ]:
            unwrap(client.post(f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/execute", json={"executorId": seed["tech_employee_id"], "remark": "\u5f00\u59cb\u6267\u884c"}))
            unwrap(client.post(f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/report", json={"reporterId": seed["tech_employee_id"], "result": result_text, "remark": "\u62a5\u544a\u5f55\u5165"}))
            ai = unwrap(client.post(f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/ai-interpret"))
            if not ai.get("summary"):
                raise RuntimeError(f"AI interpretation missing summary: {ai}")

        check_results = unwrap(client.get(f"{PROJECT2}/api/doctor/check-results/{register_id}"))
        if not check_results.get("checkRequests") or not check_results.get("inspectionRequests"):
            raise RuntimeError(f"doctor cannot read medical-tech results: {check_results}")

        inventory_before = unwrap(client.get(f"{PROJECT2}/api/drugstore/inventory", params={"drugName": seed["drug_name"], "pageNum": 1, "pageSize": 10}))
        matching_inventory = [row for row in inventory_before.get("records", []) if row.get("drugId") == seed["drug_id"]]
        if not matching_inventory:
            raise RuntimeError(f"drugstore inventory did not include seeded drug by name search: {inventory_before}")
        assert_inventory_row(matching_inventory[0], seed)
        unwrap(client.post(f"{PROJECT2}/api/drugstore/stock/in", json={"drugId": seed["drug_id"], "quantity": 20, "operatorId": seed["pharmacist_id"], "reason": "\u91c7\u8d2d\u5165\u5e93"}))
        unwrap(client.post(f"{PROJECT2}/api/drugstore/stock/check", json={"drugId": seed["drug_id"], "actualStock": 25, "operatorId": seed["pharmacist_id"], "reason": "\u6708\u5ea6\u76d8\u70b9"}))
        alerts = unwrap(client.get(f"{PROJECT2}/api/drugstore/stock/alerts", params={"threshold": 30, "pageNum": 1, "pageSize": 200}))
        if not any(row.get("drugId") == seed["drug_id"] for row in alerts.get("records", [])):
            raise RuntimeError(f"low stock alert missing checked drug: {alerts}")

        prescription_id = unwrap(client.post(f"{PROJECT2}/api/doctor/prescription", json={"registerId": register_id, "doctorId": seed["doctor_id"], "items": [{"drugId": seed["drug_id"], "usageRoute": "\u9759\u6ef4", "frequency": "\u6bcf\u65e5\u4e00\u6b21", "singleDose": "250ml", "useDays": 1, "drugNumber": 2}]}))
        unwrap(client.post(f"{PROJECT2}/api/admin/finance/charge", json={"registerId": register_id, "itemIds": [prescription_id], "itemTypes": ["PRESCRIPTION"], "chargeMethod": "CASH", "amount": "25.00"}))
        unwrap(client.post(f"{PROJECT2}/api/drugstore/dispense", json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"]}))
        unwrap(client.post(f"{PROJECT2}/api/drugstore/refund", json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"], "refundReason": "\u4e1a\u52a1\u9000\u836f"}))
        stock_records = unwrap(client.get(f"{PROJECT2}/api/drugstore/stock/records", params={"drugId": seed["drug_id"], "pageNum": 1, "pageSize": 20}))
        record_types = {row.get("recordType") for row in stock_records.get("records", [])}
        if not {"IN", "CHECK", "DISPENSE", "REFUND"}.issubset(record_types):
            raise RuntimeError(f"stock records incomplete: {stock_records}")

    db_stock = fetch_stock_and_records(seed["drug_id"])
    if db_stock["stock"] != 25:
        raise RuntimeError(f"final stock should be 25 after dispense and refund, got {db_stock}")

    print(json.dumps({
        "status": "success",
        "seed": seed,
        "register_id": register_id,
        "prescription_id": prescription_id,
        "schedule_source_id": schedule_id,
        "medical_tech_result_sections": {
            "checks": len(check_results.get("checkRequests") or []),
            "inspections": len(check_results.get("inspectionRequests") or []),
            "disposals": len(check_results.get("disposalRequests") or []),
        },
        "drug_inventory_verified": matching_inventory[0],
        "stock_records": db_stock["records"],
    }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
