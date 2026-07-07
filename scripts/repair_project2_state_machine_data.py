"""Repair historical Project2 state-machine data.

This script is for local demo/business acceptance data only. It does not hide
runtime bugs: runtime code now prevents duplicate schedule sources and duplicate
active registers. This script normalizes old rows created before those guards.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project2_db_env import get_project2_db_dsn  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DB_DSN = get_project2_db_dsn(ROOT)
ACTIVE_REGISTER_STATES = ["REGISTERED", "CHECKED_IN", "DOCTOR_RECEIVED", "ONGOING", "CONSULTING"]


def fetchall(cur: psycopg.Cursor, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def execute(cur: psycopg.Cursor, sql: str, params: tuple[Any, ...] = ()) -> int:
    cur.execute(sql, params)
    return cur.rowcount


def repair_duplicate_schedules(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    groups = fetchall(
        cur,
        """
        SELECT employee_id, deptment_id, schedule_date, noon, array_agg(id ORDER BY id) AS ids
        FROM scheduling
        WHERE schedule_status = 'NORMAL'
        GROUP BY employee_id, deptment_id, schedule_date, noon
        HAVING COUNT(*) > 1
        ORDER BY schedule_date, employee_id, noon
        """,
    )
    for group in groups:
        rows = fetchall(
            cur,
            """
            SELECT id, regist_quota, create_time
            FROM scheduling
            WHERE employee_id = %s AND deptment_id = %s AND schedule_date = %s AND noon = %s
            ORDER BY id
            """,
            (group["employee_id"], group["deptment_id"], group["schedule_date"], group["noon"]),
        )
        cur.execute(
            """
            SELECT COUNT(*) AS used
            FROM register
            WHERE employee_id = %s
              AND deptment_id = %s
              AND visit_date = %s
              AND noon = %s
              AND visit_state = ANY(%s)
            """,
            (group["employee_id"], group["deptment_id"], group["schedule_date"], group["noon"], ACTIVE_REGISTER_STATES),
        )
        used = int(cur.fetchone()["used"])
        keep = sorted(rows, key=lambda row: (row["id"]))[0]
        quota = max([used, 1] + [int(row["regist_quota"] or 0) for row in rows])
        cancel_ids = [int(row["id"]) for row in rows if row["id"] != keep["id"]]
        execute(cur, "UPDATE scheduling SET regist_quota = %s, schedule_status = 'NORMAL', update_time = NOW() WHERE id = %s", (quota, keep["id"]))
        if cancel_ids:
            execute(cur, "UPDATE scheduling SET schedule_status = 'SUSPENDED', update_time = NOW() WHERE id = ANY(%s)", (cancel_ids,))
        repaired.append({
            "slot": {
                "doctorId": group["employee_id"],
                "deptId": group["deptment_id"],
                "date": str(group["schedule_date"]),
                "noon": group["noon"],
            },
            "keptScheduleId": keep["id"],
            "quota": quota,
            "suspendedScheduleIds": cancel_ids,
        })
    return repaired


def repair_active_registers_without_schedule(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    bad = fetchall(
        cur,
        """
        SELECT r.id, r.patient_id, r.employee_id, r.deptment_id, r.visit_date, r.noon, r.visit_state
        FROM register r
        WHERE r.visit_state = ANY(%s)
          AND NOT EXISTS (
            SELECT 1 FROM scheduling s
            WHERE s.employee_id = r.employee_id
              AND s.deptment_id = r.deptment_id
              AND s.schedule_date = r.visit_date
              AND s.noon = r.noon
              AND s.schedule_status = 'NORMAL'
          )
        ORDER BY r.visit_date, r.id
        """,
        (ACTIVE_REGISTER_STATES,),
    )
    for row in bad:
        if row["visit_date"] < date.today():
            execute(cur, "UPDATE register SET visit_state = 'FINISHED', update_time = NOW() WHERE id = %s", (row["id"],))
            repaired.append({"registerId": row["id"], "action": "past_active_without_schedule_marked_finished"})
        else:
            execute(
                cur,
                """
                INSERT INTO scheduling(employee_id, deptment_id, schedule_date, noon, regist_quota, schedule_status, source_type)
                VALUES(%s, %s, %s, %s, 1, 'NORMAL', 'REPAIR')
                """,
                (row["employee_id"], row["deptment_id"], row["visit_date"], row["noon"]),
            )
            repaired.append({"registerId": row["id"], "action": "created_missing_schedule"})
    return repaired


def repair_terminal_registers_with_active_items(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    rows = fetchall(
        cur,
        """
        SELECT r.id, r.patient_id, r.employee_id, r.deptment_id, r.visit_date, r.noon, r.visit_state
        FROM register r
        WHERE r.visit_state IN ('CANCELLED','REFUNDED')
          AND (
            EXISTS (SELECT 1 FROM check_request cr WHERE cr.register_id = r.id AND cr.check_state IN ('CREATED','CHARGED','EXECUTING'))
            OR EXISTS (SELECT 1 FROM inspection_request ir WHERE ir.register_id = r.id AND ir.inspection_state IN ('CREATED','CHARGED','EXECUTING'))
            OR EXISTS (SELECT 1 FROM disposal_request dr WHERE dr.register_id = r.id AND dr.disposal_state IN ('CREATED','CHARGED','EXECUTING'))
            OR EXISTS (SELECT 1 FROM prescription p WHERE p.register_id = r.id AND p.prescription_status IN ('CREATED','CHARGED'))
          )
        ORDER BY r.id
        """,
    )
    for row in rows:
        other_active = fetchall(
            cur,
            """
            SELECT id
            FROM register
            WHERE id <> %s
              AND patient_id = %s
              AND employee_id = %s
              AND visit_date = %s
              AND visit_state = ANY(%s)
            ORDER BY id
            """,
            (row["id"], row["patient_id"], row["employee_id"], row["visit_date"], ACTIVE_REGISTER_STATES),
        )
        if other_active:
            finalized = finalize_items_under_cancelled_register(cur, row["id"])
            repaired.append({
                "registerId": row["id"],
                "action": "finalized_child_items_because_another_active_register_exists",
                "otherActiveRegisters": [r["id"] for r in other_active],
                "finalized": finalized,
            })
        else:
            execute(cur, "UPDATE register SET visit_state = 'DOCTOR_RECEIVED', update_time = NOW() WHERE id = %s", (row["id"],))
            repaired.append({
                "registerId": row["id"],
                "action": "restored_to_doctor_received_because_it_has_active_orders",
                "cancelledOtherActiveRegisters": [],
            })
    return repaired


def finalize_items_under_cancelled_register(cur: psycopg.Cursor, register_id: int) -> list[dict[str, Any]]:
    finalized: list[dict[str, Any]] = []
    request_specs = [
        ("CHECK", "check_request", "check_state", "check_info"),
        ("INSPECTION", "inspection_request", "inspection_state", "inspection_info"),
        ("DISPOSAL", "disposal_request", "disposal_state", "disposal_info"),
    ]
    for item_type, table, state_col, name_col in request_specs:
        items = fetchall(
            cur,
            f"""
            SELECT t.id, t.register_id, t.{state_col} AS state,
                   COALESCE(mt.tech_name, t.{name_col}, %s) AS item_name,
                   COALESCE(mt.tech_price, 0) AS amount
            FROM {table} t
            LEFT JOIN medical_technology mt ON mt.id = t.medical_technology_id
            WHERE t.register_id = %s AND t.{state_col} IN ('CREATED','CHARGED','EXECUTING')
            """,
            (item_type, register_id),
        )
        for item in items:
            if item["state"] == "CREATED":
                execute(cur, f"UPDATE {table} SET {state_col} = 'CANCELLED' WHERE id = %s", (item["id"],))
                finalized.append({"itemType": item_type, "itemId": item["id"], "state": "CANCELLED"})
            else:
                insert_finance_if_missing(cur, register_id, item["id"], item_type, item["item_name"], item["amount"], "REFUND", "状态机修复")
                execute(cur, f"UPDATE {table} SET {state_col} = 'REFUNDED' WHERE id = %s", (item["id"],))
                finalized.append({"itemType": item_type, "itemId": item["id"], "state": "REFUNDED"})

    prescriptions = fetchall(
        cur,
        """
        SELECT id, register_id, prescription_status, COALESCE(total_amount, 0) AS total_amount
        FROM prescription
        WHERE register_id = %s AND prescription_status IN ('CREATED','CHARGED')
        """,
        (register_id,),
    )
    for prescription in prescriptions:
        if prescription["prescription_status"] == "CREATED":
            execute(cur, "UPDATE prescription SET prescription_status = 'CANCELLED', update_time = NOW() WHERE id = %s", (prescription["id"],))
            finalized.append({"itemType": "PRESCRIPTION", "itemId": prescription["id"], "state": "CANCELLED"})
        else:
            insert_finance_if_missing(cur, register_id, prescription["id"], "PRESCRIPTION", "处方", prescription["total_amount"], "REFUND", "状态机修复")
            execute(cur, "UPDATE prescription SET prescription_status = 'REFUNDED', update_time = NOW() WHERE id = %s", (prescription["id"],))
            finalized.append({"itemType": "PRESCRIPTION", "itemId": prescription["id"], "state": "REFUNDED"})
    return finalized


def insert_finance_if_missing(cur: psycopg.Cursor, register_id: int, item_id: int, item_type: str,
                              item_name: str, amount: Decimal, record_type: str, operator: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM finance_record
        WHERE register_id = %s AND item_id = %s AND item_type = %s AND record_type = %s
        LIMIT 1
        """,
        (register_id, item_id, item_type, record_type),
    )
    if cur.fetchone():
        return False
    execute(
        cur,
        """
        INSERT INTO finance_record(record_no, register_id, item_id, item_type, item_name, amount, charge_method, record_type, operator_name)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            f"{record_type}-REPAIR-{register_id}-{item_type}-{item_id}",
            register_id,
            item_id,
            item_type,
            item_name,
            amount,
            "REPAIR" if record_type == "CHARGE" else "REFUND",
            record_type,
            operator,
        ),
    )
    return True


def repair_finance_records(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    request_specs = [
        ("CHECK", "check_request", "check_state", "check_info"),
        ("INSPECTION", "inspection_request", "inspection_state", "inspection_info"),
        ("DISPOSAL", "disposal_request", "disposal_state", "disposal_info"),
    ]
    for item_type, table, state_col, name_col in request_specs:
        records = fetchall(
            cur,
            f"""
            SELECT t.id, t.register_id, t.{state_col} AS state,
                   COALESCE(mt.tech_name, t.{name_col}, %s) AS item_name,
                   COALESCE(mt.tech_price, 0) AS amount
            FROM {table} t
            LEFT JOIN medical_technology mt ON mt.id = t.medical_technology_id
            WHERE t.{state_col} IN ('CHARGED','EXECUTING','COMPLETED','REFUNDED')
            """,
            (item_type,),
        )
        for row in records:
            if insert_finance_if_missing(cur, row["register_id"], row["id"], item_type, row["item_name"], row["amount"], "CHARGE", "状态机修复"):
                repaired.append({"itemType": item_type, "itemId": row["id"], "finance": "CHARGE"})
            if row["state"] == "REFUNDED" and insert_finance_if_missing(cur, row["register_id"], row["id"], item_type, row["item_name"], row["amount"], "REFUND", "状态机修复"):
                repaired.append({"itemType": item_type, "itemId": row["id"], "finance": "REFUND"})

    prescriptions = fetchall(
        cur,
        """
        SELECT id, register_id, prescription_status, COALESCE(total_amount, 0) AS total_amount
        FROM prescription
        WHERE prescription_status IN ('CHARGED','DISPENSED','REFUNDED')
        """,
    )
    for row in prescriptions:
        if insert_finance_if_missing(cur, row["register_id"], row["id"], "PRESCRIPTION", "处方", row["total_amount"], "CHARGE", "状态机修复"):
            repaired.append({"itemType": "PRESCRIPTION", "itemId": row["id"], "finance": "CHARGE"})
        if row["prescription_status"] == "REFUNDED" and insert_finance_if_missing(cur, row["register_id"], row["id"], "PRESCRIPTION", "处方", row["total_amount"], "REFUND", "状态机修复"):
            repaired.append({"itemType": "PRESCRIPTION", "itemId": row["id"], "finance": "REFUND"})
    return repaired


def repair_prescription_stock_records(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    details = fetchall(
        cur,
        """
        SELECT p.id AS prescription_id, p.prescription_status, p.pharmacist_id,
               pd.drug_id, pd.drug_number,
               COALESCE(SUM(CASE WHEN dsr.record_type = 'DISPENSE' THEN dsr.quantity ELSE 0 END), 0) AS dispensed_quantity,
               COALESCE(SUM(CASE WHEN dsr.record_type = 'REFUND' THEN dsr.quantity ELSE 0 END), 0) AS refunded_quantity
        FROM prescription p
        JOIN prescription_detail pd ON pd.prescription_id = p.id
        LEFT JOIN drug_stock_record dsr
          ON dsr.related_prescription_id = p.id
         AND dsr.drug_id = pd.drug_id
         AND dsr.record_type IN ('DISPENSE','REFUND')
        WHERE p.prescription_status IN ('DISPENSED','REFUNDED')
        GROUP BY p.id, p.prescription_status, p.pharmacist_id, pd.drug_id, pd.drug_number
        ORDER BY p.id, pd.drug_id
        """,
    )
    for row in details:
        drug_id = row["drug_id"]
        quantity = int(row["drug_number"] or 0)
        if quantity <= 0:
            continue
        if int(row["dispensed_quantity"] or 0) != quantity:
            cur.execute("SELECT COALESCE(stock_num, 0) AS stock FROM drug_info WHERE id = %s", (drug_id,))
            before = int(cur.fetchone()["stock"])
            after = before - quantity
            execute(cur, "UPDATE drug_info SET stock_num = %s, update_time = NOW() WHERE id = %s", (after, drug_id))
            execute(
                cur,
                """
                INSERT INTO drug_stock_record(drug_id, record_type, quantity, before_stock, after_stock, operator_id, related_prescription_id, reason)
                VALUES(%s, 'DISPENSE', %s, %s, %s, %s, %s, '状态机修复补发药流水')
                """,
                (drug_id, quantity, before, after, row["pharmacist_id"], row["prescription_id"]),
            )
            repaired.append({"prescriptionId": row["prescription_id"], "drugId": drug_id, "stock": "DISPENSE"})
        if row["prescription_status"] == "REFUNDED" and int(row["refunded_quantity"] or 0) != quantity:
            cur.execute("SELECT COALESCE(stock_num, 0) AS stock FROM drug_info WHERE id = %s", (drug_id,))
            before = int(cur.fetchone()["stock"])
            after = before + quantity
            execute(cur, "UPDATE drug_info SET stock_num = %s, update_time = NOW() WHERE id = %s", (after, drug_id))
            execute(
                cur,
                """
                INSERT INTO drug_stock_record(drug_id, record_type, quantity, before_stock, after_stock, operator_id, related_prescription_id, reason)
                VALUES(%s, 'REFUND', %s, %s, %s, %s, %s, '状态机修复补退药流水')
                """,
                (drug_id, quantity, before, after, row["pharmacist_id"], row["prescription_id"]),
            )
            repaired.append({"prescriptionId": row["prescription_id"], "drugId": drug_id, "stock": "REFUND"})
    return repaired


def main() -> None:
    result: dict[str, Any] = {}
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            result["duplicateSchedules"] = repair_duplicate_schedules(cur)
            result["activeRegistersWithoutSchedule"] = repair_active_registers_without_schedule(cur)
            result["terminalRegistersWithActiveItems"] = repair_terminal_registers_with_active_items(cur)
            result["financeRecords"] = repair_finance_records(cur)
            result["prescriptionStockRecords"] = repair_prescription_stock_records(cur)
        conn.commit()
    print(json.dumps({"status": "PASS", "repairs": result}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
