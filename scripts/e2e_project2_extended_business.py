"""Validate Project2 medical-tech, drug inventory and schedule-source workflows."""

from __future__ import annotations

import json
import os
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row


PROJECT2 = os.getenv("PROJECT2_BASE_URL", "http://127.0.0.1:8092")
DB_DSN = os.getenv("PROJECT2_DB_DSN", "postgresql://postgres:postgres@localhost:5432/hospital")


def unwrap(response: httpx.Response) -> Any:
    response.raise_for_status()
    if not response.text.strip():
        return None
    return response.json()


def require_tables(conn: psycopg.Connection[Any]) -> None:
    required = {
        "department",
        "employee",
        "regist_level",
        "settle_category",
        "scheduling",
        "patient",
        "register",
        "medical_technology",
        "check_request",
        "inspection_request",
        "disposal_request",
        "drug_info",
        "prescription",
        "prescription_detail",
        "drug_stock_record",
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
        raise RuntimeError(
            "Project2 schema missing tables: "
            + ", ".join(missing)
            + ". Run Project2/sql/init_project2_db.ps1 before e2e validation."
        )
    with conn.cursor() as cur:
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
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        require_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO department(dept_code, dept_name, dept_type, delmark)
                VALUES (%s, 'Extended神经影像科', 'MEDICAL_TECH', TRUE)
                RETURNING id
                """,
                (f"EXT-DEPT-{suffix}",),
            )
            dept_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO regist_level(regist_code, regist_name, regist_fee, regist_quota, is_expert, sequence_no, delmark)
                VALUES (%s, 'Extended普通号', 20.00, 50, FALSE, 1, TRUE)
                RETURNING id
                """,
                (f"EXT-RL-{suffix}",),
            )
            regist_level_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO settle_category(settle_code, settle_name, sequence_no, delmark)
                VALUES (%s, '自费', 1, TRUE)
                RETURNING id
                """,
                (f"EXT-SC-{suffix}",),
            )
            settle_category_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO employee(deptment_id, regist_level_id, realname, role_type, title_level, password_hash, phone, delmark)
                VALUES (%s, %s, 'Extended医生', 'DOCTOR', '主治医师', 'e2e', '13900001001', TRUE)
                RETURNING id
                """,
                (dept_id, regist_level_id),
            )
            doctor_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark)
                VALUES (%s, 'Extended医技', 'MEDICAL_TECH', '技师', 'e2e', '13900001002', TRUE)
                RETURNING id
                """,
                (dept_id,),
            )
            tech_employee_id = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark)
                VALUES (%s, 'Extended药师', 'PHARMACIST', '药师', 'e2e', '13900001003', TRUE)
                RETURNING id
                """,
                (dept_id,),
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
                ("CHECK", "Extended头颅CT", Decimal("180.00")),
                ("INSPECTION", "Extended血常规", Decimal("25.00")),
                ("DISPOSAL", "Extended清创换药", Decimal("35.00")),
            ]:
                cur.execute(
                    """
                    INSERT INTO medical_technology(tech_code, tech_name, tech_format, tech_price, tech_type, price_type, deptment_id)
                    VALUES (%s, %s, '次', %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (f"EXT-{tech_type}-{suffix}", name, price, tech_type, "医技费", dept_id),
                )
                tech_ids[tech_type] = int(cur.fetchone()["id"])
            cur.execute(
                """
                INSERT INTO drug_info(drug_code, drug_name, drug_format, drug_unit, stock_num, drug_price, manufacturer, drug_type)
                VALUES (%s, 'Extended甘露醇注射液', '250ml', '瓶', 8, 12.50, 'Extended药厂', '西药')
                RETURNING id
                """,
                (f"EXT-DRUG-{suffix}",),
            )
            drug_id = int(cur.fetchone()["id"])
        conn.commit()
    return {
        "suffix": suffix,
        "today": today.isoformat(),
        "tomorrow": (today + timedelta(days=1)).isoformat(),
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


def main() -> None:
    seed = seed_data()
    numeric_suffix = str(int(seed["suffix"], 16) % 100000).zfill(5)
    register_id: int
    prescription_id: int

    with httpx.Client(timeout=60) as client:
        health = unwrap(client.get(f"{PROJECT2}/actuator/health"))
        if health.get("status") != "UP":
            raise RuntimeError(f"Project2 health is not UP: {health}")

        schedule_id = unwrap(
            client.post(
                f"{PROJECT2}/api/schedule/sources",
                json={
                    "doctorId": seed["doctor_id"],
                    "deptId": seed["dept_id"],
                    "scheduleDate": seed["tomorrow"],
                    "noon": "PM",
                    "registQuota": 12,
                    "sourceType": "MANUAL",
                },
            )
        )
        unwrap(client.put(f"{PROJECT2}/api/schedule/sources/{schedule_id}/quota", json={"registQuota": 18}))
        unwrap(client.put(f"{PROJECT2}/api/schedule/sources/{schedule_id}/suspend", json={"reason": "临时停诊演练"}))
        unwrap(client.put(f"{PROJECT2}/api/schedule/sources/{schedule_id}/resume", json={"reason": "恢复接诊"}))
        sources = unwrap(
            client.get(
                f"{PROJECT2}/api/schedule/sources",
                params={"deptId": seed["dept_id"], "startDate": seed["tomorrow"], "endDate": seed["tomorrow"]},
            )
        )
        if not any(item.get("scheduleId") == schedule_id and item.get("registQuota") == 18 for item in sources.get("records", [])):
            raise RuntimeError(f"created schedule source not visible or quota not updated: {sources}")

        register_id = unwrap(
            client.post(
                f"{PROJECT2}/api/patient/register",
                json={
                    "realName": "Extended业务患者",
                    "gender": "M",
                    "cardNumber": "110101197505" + numeric_suffix + "X",
                    "birthdate": "1975-05-05",
                    "homeAddress": "Project2 Extended E2E",
                    "phone": "13900001111",
                    "deptId": seed["dept_id"],
                    "doctorId": seed["doctor_id"],
                    "visitDate": seed["today"],
                    "noon": "AM",
                    "registLevelId": seed["regist_level_id"],
                    "settleCategoryId": seed["settle_category_id"],
                    "registMethod": "WINDOW",
                },
            )
        )
        unwrap(client.put(f"{PROJECT2}/api/doctor/patients/{register_id}/receive"))
        unwrap(
            client.post(
                f"{PROJECT2}/api/doctor/check-request",
                json={
                    "registerId": register_id,
                    "items": [{"medicalTechnologyId": seed["check_tech_id"], "checkInfo": "头颅CT", "checkPosition": "head"}],
                },
            )
        )
        unwrap(
            client.post(
                f"{PROJECT2}/api/doctor/inspection-request",
                json={
                    "registerId": register_id,
                    "items": [{"medicalTechnologyId": seed["inspection_tech_id"], "inspectionInfo": "血常规", "inspectionPosition": "blood"}],
                },
            )
        )
        unwrap(
            client.post(
                f"{PROJECT2}/api/doctor/disposal-request",
                json={
                    "registerId": register_id,
                    "items": [{"medicalTechnologyId": seed["disposal_tech_id"], "disposalInfo": "清创换药", "disposalPosition": "head"}],
                },
            )
        )

        with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM check_request WHERE register_id = %s ORDER BY id DESC LIMIT 1", (register_id,))
                check_id = int(cur.fetchone()["id"])
                cur.execute("SELECT id FROM inspection_request WHERE register_id = %s ORDER BY id DESC LIMIT 1", (register_id,))
                inspection_id = int(cur.fetchone()["id"])
                cur.execute("SELECT id FROM disposal_request WHERE register_id = %s ORDER BY id DESC LIMIT 1", (register_id,))
                disposal_id = int(cur.fetchone()["id"])

        unwrap(
            client.post(
                f"{PROJECT2}/api/admin/finance/charge",
                json={
                    "registerId": register_id,
                    "itemIds": [check_id, inspection_id, disposal_id],
                    "itemTypes": ["CHECK", "INSPECTION", "DISPOSAL"],
                    "chargeMethod": "CASH",
                    "amount": "240.00",
                },
            )
        )
        tasks = unwrap(client.get(f"{PROJECT2}/api/medical-tech/tasks", params={"registerId": register_id, "state": "CHARGED"}))
        if len(tasks.get("records", [])) < 3:
            raise RuntimeError(f"medical-tech charged tasks not visible: {tasks}")
        for item_type, item_id, result_text in [
            ("CHECK", check_id, "CT未见明显急性出血征象"),
            ("INSPECTION", inspection_id, "白细胞计数轻度升高"),
            ("DISPOSAL", disposal_id, "伤口清洁换药完成"),
        ]:
            unwrap(
                client.post(
                    f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/execute",
                    json={"executorId": seed["tech_employee_id"], "remark": "开始执行"},
                )
            )
            unwrap(
                client.post(
                    f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/report",
                    json={"reporterId": seed["tech_employee_id"], "result": result_text, "remark": "报告录入"},
                )
            )
            ai = unwrap(client.post(f"{PROJECT2}/api/medical-tech/tasks/{item_type}/{item_id}/ai-interpret"))
            if not ai.get("summary"):
                raise RuntimeError(f"AI interpretation missing summary: {ai}")
        check_results = unwrap(client.get(f"{PROJECT2}/api/doctor/check-results/{register_id}"))
        if not check_results.get("checkRequests") or not check_results.get("inspectionRequests"):
            raise RuntimeError(f"doctor cannot read medical-tech results: {check_results}")

        inventory_before = unwrap(client.get(f"{PROJECT2}/api/drugstore/inventory", params={"pageNum": 1, "pageSize": 10}))
        if not any(row.get("drugId") == seed["drug_id"] for row in inventory_before.get("records", [])):
            raise RuntimeError(f"drugstore inventory did not include seeded drug: {inventory_before}")
        unwrap(
            client.post(
                f"{PROJECT2}/api/drugstore/stock/in",
                json={"drugId": seed["drug_id"], "quantity": 20, "operatorId": seed["pharmacist_id"], "reason": "采购入库"},
            )
        )
        unwrap(
            client.post(
                f"{PROJECT2}/api/drugstore/stock/check",
                json={"drugId": seed["drug_id"], "actualStock": 25, "operatorId": seed["pharmacist_id"], "reason": "月度盘点"},
            )
        )
        alerts = unwrap(client.get(f"{PROJECT2}/api/drugstore/stock/alerts", params={"threshold": 30}))
        if not any(row.get("drugId") == seed["drug_id"] for row in alerts.get("records", [])):
            raise RuntimeError(f"low stock alert missing checked drug: {alerts}")

        prescription_id = unwrap(
            client.post(
                f"{PROJECT2}/api/doctor/prescription",
                json={
                    "registerId": register_id,
                    "doctorId": seed["doctor_id"],
                    "items": [
                        {
                            "drugId": seed["drug_id"],
                            "usageRoute": "静滴",
                            "frequency": "每日一次",
                            "singleDose": "250ml",
                            "useDays": 1,
                            "drugNumber": 2,
                        }
                    ],
                },
            )
        )
        unwrap(
            client.post(
                f"{PROJECT2}/api/admin/finance/charge",
                json={"registerId": register_id, "itemIds": [prescription_id], "itemTypes": ["PRESCRIPTION"], "chargeMethod": "CASH", "amount": "25.00"},
            )
        )
        unwrap(client.post(f"{PROJECT2}/api/drugstore/dispense", json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"]}))
        unwrap(client.post(f"{PROJECT2}/api/drugstore/refund", json={"prescriptionId": prescription_id, "pharmacistId": seed["pharmacist_id"], "refundReason": "业务验收退药"}))
        stock_records = unwrap(client.get(f"{PROJECT2}/api/drugstore/stock/records", params={"drugId": seed["drug_id"], "pageNum": 1, "pageSize": 20}))
        record_types = {row.get("recordType") for row in stock_records.get("records", [])}
        if not {"IN", "CHECK", "DISPENSE", "REFUND"}.issubset(record_types):
            raise RuntimeError(f"stock records incomplete: {stock_records}")

    db_stock = fetch_stock_and_records(seed["drug_id"])
    if db_stock["stock"] != 25:
        raise RuntimeError(f"final stock should be 25 after dispense and refund, got {db_stock}")

    print(
        json.dumps(
            {
                "status": "success",
                "register_id": register_id,
                "schedule_id": schedule_id,
                "medical_tech": {
                    "check_id": check_id,
                    "inspection_id": inspection_id,
                    "disposal_id": disposal_id,
                },
                "drug_id": seed["drug_id"],
                "prescription_id": prescription_id,
                "stock": db_stock,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
