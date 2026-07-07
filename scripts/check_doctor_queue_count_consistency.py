import json
import os
import sys

import requests


BASE_URL = os.getenv("PROJECT2_BASE_URL", "http://127.0.0.1:8092")
USERNAME = os.getenv("PROJECT2_DOCTOR_USERNAME", "doctor")
PASSWORD = os.getenv("PROJECT2_DOCTOR_PASSWORD", "123456")


def fail(message: str) -> None:
    print(message)
    sys.exit(1)


def unwrap(response: requests.Response):
    try:
        payload = response.json()
    except Exception:
        payload = response.text
    if not response.ok:
        fail(f"HTTP {response.status_code}: {response.url}\n{payload}")
    return payload


def main() -> None:
    session = requests.Session()
    login = unwrap(
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": USERNAME, "password": PASSWORD, "loginType": "DOCTOR"},
            timeout=10,
        )
    )
    token = login.get("token")
    doctor_id = login.get("employeeId")
    if not token or not doctor_id:
        fail(f"doctor login did not return token/employeeId: {login}")
    session.headers.update({"Authorization": f"Bearer {token}"})

    statistics = unwrap(session.get(f"{BASE_URL}/api/doctor/statistics", params={"doctorId": doctor_id}, timeout=10))
    summary = unwrap(session.get(f"{BASE_URL}/api/doctor/dashboard/summary", params={"doctorId": doctor_id}, timeout=10))

    queue_totals = {}
    for label, state in {
        "pendingCount": "REGISTERED",
        "consultingCount": "DOCTOR_RECEIVED",
        "finishedCount": "DIAGNOSIS_DONE",
    }.items():
        payload = unwrap(
            session.get(
                f"{BASE_URL}/api/doctor/patients",
                params={"doctorId": doctor_id, "visitState": state, "pageNum": 1, "pageSize": 50},
                timeout=10,
            )
        )
        queue_totals[label] = int(payload.get("total") or 0)

    failures = []
    for key, queue_count in queue_totals.items():
        stat_key = "finishedToday" if key == "finishedCount" else key
        stat_value = int(statistics.get(key) or 0)
        summary_value = int(summary.get(stat_key) or 0)
        if stat_value != queue_count:
            failures.append(f"statistics.{key}={stat_value}, queue.{key}={queue_count}")
        if summary_value != queue_count:
            failures.append(f"summary.{stat_key}={summary_value}, queue.{key}={queue_count}")

    evidence = {
        "doctorId": doctor_id,
        "statistics": statistics,
        "summary": summary,
        "queueTotals": queue_totals,
    }
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    if failures:
        fail("Doctor queue count mismatch:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
