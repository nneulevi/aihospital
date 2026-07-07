"""Audit Project2 state machines from database facts.

This is intentionally read-only. It verifies the business state machines used
by patient, doctor, admin/finance, medical-tech, report-facing AI rows and
drugstore modules.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project2_db_env import get_project2_db_dsn  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DB_DSN = get_project2_db_dsn(ROOT)

ACTIVE_REGISTER_STATES = {"REGISTERED", "CHECKED_IN", "DOCTOR_RECEIVED", "ONGOING", "CONSULTING"}
REGISTER_STATES = ACTIVE_REGISTER_STATES | {"DIAGNOSIS_DONE", "DIAGNOSED", "FINISHED", "CANCELLED", "REFUNDED"}
REQUEST_STATES = {"CREATED", "CHARGED", "EXECUTING", "COMPLETED", "REFUNDED", "CANCELLED"}
PRESCRIPTION_STATES = {"CREATED", "CHARGED", "DISPENSED", "REFUNDED", "CANCELLED"}
SCHEDULE_STATES = {"NORMAL", "CANCELLED", "SUSPENDED"}
STOCK_RECORD_TYPES = {"IN", "CHECK", "DISPENSE", "REFUND"}
FINANCE_RECORD_TYPES = {"CHARGE", "REFUND"}
FINANCE_ITEM_TYPES = {"CHECK", "INSPECTION", "DISPOSAL", "PRESCRIPTION", "DRUG"}
AI_REPORT_STATES = {"DRAFT", "CONFIRMED", "RELEASED", "ARCHIVED"}


def d(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def rows(cur: psycopg.Cursor, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def one(cur: psycopg.Cursor, sql: str, params: tuple[Any, ...] = ()) -> Any:
    cur.execute(sql, params)
    return cur.fetchone()


def add_if(problems: list[dict[str, Any]], name: str, detail: Any, condition: bool = True) -> None:
    if condition:
        problems.append({"check": name, "detail": detail})


def assert_status_enums(cur: psycopg.Cursor, problems: list[dict[str, Any]]) -> None:
    checks = [
        ("register.visit_state", "register", "visit_state", REGISTER_STATES),
        ("scheduling.schedule_status", "scheduling", "schedule_status", SCHEDULE_STATES),
        ("check_request.check_state", "check_request", "check_state", REQUEST_STATES),
        ("inspection_request.inspection_state", "inspection_request", "inspection_state", REQUEST_STATES),
        ("disposal_request.disposal_state", "disposal_request", "disposal_state", REQUEST_STATES),
        ("prescription.prescription_status", "prescription", "prescription_status", PRESCRIPTION_STATES),
        ("drug_stock_record.record_type", "drug_stock_record", "record_type", STOCK_RECORD_TYPES),
        ("finance_record.record_type", "finance_record", "record_type", FINANCE_RECORD_TYPES),
        ("finance_record.item_type", "finance_record", "item_type", FINANCE_ITEM_TYPES),
        ("ai_generated_report.status", "ai_generated_report", "status", AI_REPORT_STATES),
    ]
    for label, table, column, allowed in checks:
        bad = rows(
            cur,
            f"""
            SELECT {column} AS value, COUNT(*) AS count
            FROM {table}
            WHERE {column} IS NOT NULL AND {column} <> '' AND {column} <> ALL(%s)
            GROUP BY {column}
            ORDER BY count DESC, value
            """,
            (list(allowed),),
        )
        add_if(problems, f"非法状态枚举: {label}", bad, bool(bad))


def assert_register_state_machine(cur: psycopg.Cursor, problems: list[dict[str, Any]]) -> None:
    duplicated = rows(
        cur,
        """
        SELECT patient_id, employee_id, visit_date, COUNT(*) AS active_count, array_agg(id ORDER BY id) AS register_ids
        FROM register
        WHERE visit_state = ANY(%s)
        GROUP BY patient_id, employee_id, visit_date
        HAVING COUNT(*) > 1
        ORDER BY visit_date DESC, patient_id, employee_id
        """,
        (list(ACTIVE_REGISTER_STATES),),
    )
    add_if(problems, "同一患者同一医生同日存在多个活跃挂号", duplicated, bool(duplicated))

    over_quota = rows(
        cur,
        """
        SELECT r.deptment_id, r.employee_id, r.visit_date, r.noon,
               COUNT(*) AS active_count, MAX(s.regist_quota) AS quota,
               array_agg(r.id ORDER BY r.id) AS register_ids
        FROM register r
        JOIN scheduling s
          ON s.employee_id = r.employee_id
         AND s.deptment_id = r.deptment_id
         AND s.schedule_date = r.visit_date
         AND s.noon = r.noon
         AND s.schedule_status = 'NORMAL'
        WHERE r.visit_state = ANY(%s)
        GROUP BY r.deptment_id, r.employee_id, r.visit_date, r.noon
        HAVING COUNT(*) > MAX(s.regist_quota)
        ORDER BY r.visit_date DESC
        """,
        (list(ACTIVE_REGISTER_STATES),),
    )
    add_if(problems, "活跃挂号数量超过号源配额", over_quota, bool(over_quota))

    no_schedule = rows(
        cur,
        """
        SELECT r.id, r.patient_id, r.employee_id, r.deptment_id, r.visit_date, r.noon, r.visit_state
        FROM register r
        WHERE r.visit_state = ANY(%s)
          AND NOT EXISTS (
            SELECT 1
            FROM scheduling s
            WHERE s.employee_id = r.employee_id
              AND s.deptment_id = r.deptment_id
              AND s.schedule_date = r.visit_date
              AND s.noon = r.noon
              AND s.schedule_status = 'NORMAL'
          )
        ORDER BY r.visit_date DESC, r.id DESC
        LIMIT 50
        """,
        (list(ACTIVE_REGISTER_STATES),),
    )
    add_if(problems, "活跃挂号没有对应 NORMAL 号源", no_schedule, bool(no_schedule))

    terminal_with_active_orders = rows(
        cur,
        """
        SELECT r.id, r.visit_state,
               COUNT(DISTINCT cr.id) FILTER (WHERE cr.check_state IN ('CREATED','CHARGED','EXECUTING')) AS active_checks,
               COUNT(DISTINCT ir.id) FILTER (WHERE ir.inspection_state IN ('CREATED','CHARGED','EXECUTING')) AS active_inspections,
               COUNT(DISTINCT dr.id) FILTER (WHERE dr.disposal_state IN ('CREATED','CHARGED','EXECUTING')) AS active_disposals,
               COUNT(DISTINCT p.id) FILTER (WHERE p.prescription_status IN ('CREATED','CHARGED')) AS active_prescriptions
        FROM register r
        LEFT JOIN check_request cr ON cr.register_id = r.id
        LEFT JOIN inspection_request ir ON ir.register_id = r.id
        LEFT JOIN disposal_request dr ON dr.register_id = r.id
        LEFT JOIN prescription p ON p.register_id = r.id
        WHERE r.visit_state IN ('CANCELLED','REFUNDED')
        GROUP BY r.id, r.visit_state
        HAVING COUNT(DISTINCT cr.id) FILTER (WHERE cr.check_state IN ('CREATED','CHARGED','EXECUTING')) > 0
            OR COUNT(DISTINCT ir.id) FILTER (WHERE ir.inspection_state IN ('CREATED','CHARGED','EXECUTING')) > 0
            OR COUNT(DISTINCT dr.id) FILTER (WHERE dr.disposal_state IN ('CREATED','CHARGED','EXECUTING')) > 0
            OR COUNT(DISTINCT p.id) FILTER (WHERE p.prescription_status IN ('CREATED','CHARGED')) > 0
        ORDER BY r.id DESC
        """,
    )
    add_if(problems, "已取消/已退号挂号仍有关联未终结项目", terminal_with_active_orders, bool(terminal_with_active_orders))


def assert_request_charge_state(cur: psycopg.Cursor, problems: list[dict[str, Any]]) -> None:
    specs = [
        ("CHECK", "check_request", "check_state", "check_info"),
        ("INSPECTION", "inspection_request", "inspection_state", "inspection_info"),
        ("DISPOSAL", "disposal_request", "disposal_state", "disposal_info"),
    ]
    for item_type, table, state_col, name_col in specs:
        blanks = rows(
            cur,
            f"""
            SELECT id, register_id, {name_col} AS item_name, {state_col} AS state
            FROM {table}
            WHERE COALESCE(TRIM({name_col}), '') = ''
            LIMIT 50
            """,
        )
        add_if(problems, f"{item_type} 存在空项目名称", blanks, bool(blanks))

        charged_without_finance = rows(
            cur,
            f"""
            SELECT t.id, t.register_id, t.{state_col} AS state
            FROM {table} t
            WHERE t.{state_col} IN ('CHARGED','EXECUTING','COMPLETED','REFUNDED')
              AND NOT EXISTS (
                SELECT 1 FROM finance_record fr
                WHERE fr.register_id = t.register_id
                  AND fr.item_id = t.id
                  AND fr.item_type = %s
                  AND fr.record_type = 'CHARGE'
              )
            ORDER BY t.id DESC
            LIMIT 50
            """,
            (item_type,),
        )
        add_if(problems, f"{item_type} 已缴费/执行/完成但缺少 CHARGE 财务流水", charged_without_finance, bool(charged_without_finance))

        refunded_without_finance = rows(
            cur,
            f"""
            SELECT t.id, t.register_id, t.{state_col} AS state
            FROM {table} t
            WHERE t.{state_col} = 'REFUNDED'
              AND NOT EXISTS (
                SELECT 1 FROM finance_record fr
                WHERE fr.register_id = t.register_id
                  AND fr.item_id = t.id
                  AND fr.item_type = %s
                  AND fr.record_type = 'REFUND'
              )
            ORDER BY t.id DESC
            LIMIT 50
            """,
            (item_type,),
        )
        add_if(problems, f"{item_type} 已退费但缺少 REFUND 财务流水", refunded_without_finance, bool(refunded_without_finance))

        created_with_charge = rows(
            cur,
            f"""
            SELECT t.id, t.register_id, t.{state_col} AS state
            FROM {table} t
            WHERE t.{state_col} = 'CREATED'
              AND EXISTS (
                SELECT 1 FROM finance_record fr
                WHERE fr.register_id = t.register_id
                  AND fr.item_id = t.id
                  AND fr.item_type = %s
                  AND fr.record_type = 'CHARGE'
              )
            ORDER BY t.id DESC
            LIMIT 50
            """,
            (item_type,),
        )
        add_if(problems, f"{item_type} 仍待缴费但已有 CHARGE 财务流水", created_with_charge, bool(created_with_charge))


def assert_prescription_and_drug_state(cur: psycopg.Cursor, problems: list[dict[str, Any]]) -> None:
    invalid_details = rows(
        cur,
        """
        SELECT pd.id, pd.prescription_id, pd.drug_id, pd.drug_number
        FROM prescription_detail pd
        LEFT JOIN drug_info d ON d.id = pd.drug_id
        WHERE d.id IS NULL OR COALESCE(pd.drug_number, 0) <= 0
        ORDER BY pd.id DESC
        LIMIT 50
        """,
    )
    add_if(problems, "处方明细药品不存在或数量非法", invalid_details, bool(invalid_details))

    charged_without_finance = rows(
        cur,
        """
        SELECT p.id, p.register_id, p.prescription_status
        FROM prescription p
        WHERE p.prescription_status IN ('CHARGED','DISPENSED','REFUNDED')
          AND NOT EXISTS (
            SELECT 1 FROM finance_record fr
            WHERE fr.register_id = p.register_id
              AND fr.item_id = p.id
              AND fr.item_type = 'PRESCRIPTION'
              AND fr.record_type = 'CHARGE'
          )
        ORDER BY p.id DESC
        LIMIT 50
        """,
    )
    add_if(problems, "处方已缴费/发药/退药但缺少 CHARGE 财务流水", charged_without_finance, bool(charged_without_finance))

    refunded_without_finance = rows(
        cur,
        """
        SELECT p.id, p.register_id, p.prescription_status
        FROM prescription p
        WHERE p.prescription_status = 'REFUNDED'
          AND NOT EXISTS (
            SELECT 1 FROM finance_record fr
            WHERE fr.register_id = p.register_id
              AND fr.item_id = p.id
              AND fr.item_type = 'PRESCRIPTION'
              AND fr.record_type = 'REFUND'
          )
        ORDER BY p.id DESC
        LIMIT 50
        """,
    )
    add_if(problems, "处方已退药但缺少 REFUND 财务流水", refunded_without_finance, bool(refunded_without_finance))

    stock_negative = rows(
        cur,
        """
        SELECT id, drug_code, drug_name, stock_num
        FROM drug_info
        WHERE COALESCE(stock_num, 0) < 0
        ORDER BY id
        """,
    )
    add_if(problems, "药品库存为负数", stock_negative, bool(stock_negative))

    bad_stock_delta = rows(
        cur,
        """
        SELECT id, drug_id, record_type, quantity, before_stock, after_stock
        FROM drug_stock_record
        WHERE COALESCE(quantity, 0) < 0
           OR (record_type = 'IN' AND after_stock <> before_stock + quantity)
           OR (record_type = 'DISPENSE' AND after_stock <> before_stock - quantity)
           OR (record_type = 'REFUND' AND after_stock <> before_stock + quantity)
           OR (record_type = 'CHECK' AND quantity <> ABS(after_stock - before_stock))
        ORDER BY id DESC
        LIMIT 100
        """,
    )
    add_if(problems, "药品库存流水 before/after/quantity 不一致", bad_stock_delta, bool(bad_stock_delta))

    latest_stock_mismatch = rows(
        cur,
        """
        WITH latest AS (
            SELECT DISTINCT ON (drug_id) drug_id, after_stock, id AS stock_record_id
            FROM drug_stock_record
            ORDER BY drug_id, create_time DESC, id DESC
        )
        SELECT d.id AS drug_id, d.drug_name, d.stock_num, l.after_stock, l.stock_record_id
        FROM drug_info d
        JOIN latest l ON l.drug_id = d.id
        WHERE COALESCE(d.stock_num, 0) <> COALESCE(l.after_stock, 0)
        ORDER BY d.id
        LIMIT 100
        """,
    )
    add_if(problems, "药品当前库存与最新库存流水 after_stock 不一致", latest_stock_mismatch, bool(latest_stock_mismatch))

    dispensed_missing_stock_records = rows(
        cur,
        """
        SELECT p.id AS prescription_id, p.prescription_status, pd.drug_id, pd.drug_number,
               COALESCE(SUM(CASE WHEN dsr.record_type = 'DISPENSE' THEN dsr.quantity ELSE 0 END), 0) AS dispensed_quantity,
               COALESCE(SUM(CASE WHEN dsr.record_type = 'REFUND' THEN dsr.quantity ELSE 0 END), 0) AS refunded_quantity
        FROM prescription p
        JOIN prescription_detail pd ON pd.prescription_id = p.id
        LEFT JOIN drug_stock_record dsr
          ON dsr.related_prescription_id = p.id
         AND dsr.drug_id = pd.drug_id
         AND dsr.record_type IN ('DISPENSE','REFUND')
        WHERE p.prescription_status IN ('DISPENSED','REFUNDED')
        GROUP BY p.id, p.prescription_status, pd.drug_id, pd.drug_number
        HAVING COALESCE(SUM(CASE WHEN dsr.record_type = 'DISPENSE' THEN dsr.quantity ELSE 0 END), 0) <> pd.drug_number
            OR (p.prescription_status = 'REFUNDED' AND COALESCE(SUM(CASE WHEN dsr.record_type = 'REFUND' THEN dsr.quantity ELSE 0 END), 0) <> pd.drug_number)
            OR (p.prescription_status = 'DISPENSED' AND COALESCE(SUM(CASE WHEN dsr.record_type = 'REFUND' THEN dsr.quantity ELSE 0 END), 0) <> 0)
        ORDER BY p.id DESC
        LIMIT 100
        """,
    )
    add_if(problems, "处方状态与发药/退药库存流水不一致", dispensed_missing_stock_records, bool(dispensed_missing_stock_records))


def assert_schedule_state(cur: psycopg.Cursor, problems: list[dict[str, Any]]) -> None:
    duplicate_schedules = rows(
        cur,
        """
        SELECT employee_id, deptment_id, schedule_date, noon, COUNT(*) AS n, array_agg(id ORDER BY id) AS schedule_ids
        FROM scheduling
        WHERE schedule_status = 'NORMAL'
        GROUP BY employee_id, deptment_id, schedule_date, noon
        HAVING COUNT(*) > 1
        ORDER BY schedule_date DESC, employee_id
        LIMIT 100
        """,
    )
    add_if(problems, "同一医生同一科室同日同午别存在多个 NORMAL 排班", duplicate_schedules, bool(duplicate_schedules))

    invalid_quota = rows(
        cur,
        """
        SELECT id, employee_id, deptment_id, schedule_date, noon, regist_quota, schedule_status
        FROM scheduling
        WHERE schedule_status = 'NORMAL' AND COALESCE(regist_quota, 0) <= 0
        ORDER BY schedule_date DESC
        LIMIT 100
        """,
    )
    add_if(problems, "NORMAL 排班号源数小于等于 0", invalid_quota, bool(invalid_quota))


def assert_ai_report_state(cur: psycopg.Cursor, problems: list[dict[str, Any]]) -> None:
    confirmed_without_final = rows(
        cur,
        """
        SELECT id, request_id, register_id, status, is_confirmed, confirmed_by, confirmed_time
        FROM ai_generated_report
        WHERE (status IN ('CONFIRMED','RELEASED','ARCHIVED') OR is_confirmed = 1)
          AND COALESCE(TRIM(final_content), '') = ''
        ORDER BY id DESC
        LIMIT 50
        """,
    )
    add_if(problems, "AI 报告已确认/发布但 final_content 为空", confirmed_without_final, bool(confirmed_without_final))


def main() -> None:
    problems: list[dict[str, Any]] = []
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            assert_status_enums(cur, problems)
            assert_register_state_machine(cur, problems)
            assert_request_charge_state(cur, problems)
            assert_prescription_and_drug_state(cur, problems)
            assert_schedule_state(cur, problems)
            assert_ai_report_state(cur, problems)

    output = {
        "status": "PASS" if not problems else "FAIL",
        "problemCount": len(problems),
        "problems": problems,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
