"""Repair legacy duplicate active register rows in Project2.

Business invariant:
one patient can have at most one active register for one doctor on one date.

The runtime code prevents new duplicates. This script repairs historical dirty
data by keeping the row that is furthest along in the visit workflow and
cancelling the remaining active rows in the same patient/doctor/date group.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project2_db_env import get_project2_db_dsn  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DB_DSN = get_project2_db_dsn(ROOT)

ACTIVE_STATES = ["REGISTERED", "CHECKED_IN", "DOCTOR_RECEIVED", "ONGOING", "CONSULTING"]
STATE_RANK = {
    "REGISTERED": 1,
    "CHECKED_IN": 2,
    "DOCTOR_RECEIVED": 3,
    "ONGOING": 4,
    "CONSULTING": 5,
}


def choose_keep(rows: list[dict]) -> dict:
    return sorted(
        rows,
        key=lambda row: (
            STATE_RANK.get(str(row["visit_state"]), 0),
            row["update_time"] or row["create_time"],
            row["id"],
        ),
        reverse=True,
    )[0]


def main() -> None:
    repaired: list[dict] = []
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT patient_id, employee_id, visit_date
                FROM register
                WHERE visit_state = ANY(%s)
                GROUP BY patient_id, employee_id, visit_date
                HAVING COUNT(*) > 1
                ORDER BY visit_date, patient_id, employee_id
                """,
                (ACTIVE_STATES,),
            )
            groups = cur.fetchall()
            for group in groups:
                cur.execute(
                    """
                    SELECT id, patient_id, employee_id, visit_date, noon, visit_state, create_time, update_time
                    FROM register
                    WHERE patient_id = %s
                      AND employee_id = %s
                      AND visit_date = %s
                      AND visit_state = ANY(%s)
                    ORDER BY id
                    """,
                    (group["patient_id"], group["employee_id"], group["visit_date"], ACTIVE_STATES),
                )
                rows = [dict(row) for row in cur.fetchall()]
                keep = choose_keep(rows)
                cancel_ids = [int(row["id"]) for row in rows if row["id"] != keep["id"]]
                if cancel_ids:
                    cur.execute(
                        """
                        UPDATE register
                        SET visit_state = 'CANCELLED', update_time = CURRENT_TIMESTAMP
                        WHERE id = ANY(%s)
                        """,
                        (cancel_ids,),
                    )
                repaired.append(
                    {
                        "patientId": group["patient_id"],
                        "doctorId": group["employee_id"],
                        "visitDate": str(group["visit_date"]),
                        "keptRegisterId": keep["id"],
                        "keptState": keep["visit_state"],
                        "cancelledRegisterIds": cancel_ids,
                    }
                )
        conn.commit()

    print(json.dumps({"status": "PASS", "repairedGroups": repaired}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
