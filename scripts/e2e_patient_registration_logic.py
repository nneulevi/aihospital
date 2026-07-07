import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta


BASE = "http://127.0.0.1:8092/api"


def request(method: str, path: str, data=None, query=None):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
    body = None
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else None


def post_sse(path: str, data=None):
    url = BASE + path
    body = json.dumps(data or {}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream",
        },
    )
    events = []
    current_event = None
    with urllib.request.urlopen(req, timeout=90) as resp:
        for raw in resp:
            line = raw.decode("utf-8").rstrip("\n")
            if line.startswith("event:"):
                current_event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                payload_text = line.split(":", 1)[1].strip()
                payload = json.loads(payload_text) if payload_text else {}
                events.append((current_event, payload))
    return events


def expect(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def expect_http_error(method: str, path: str, data=None, query=None):
    try:
        request(method, path, data=data, query=query)
    except urllib.error.HTTPError as exc:
        expect(exc.code >= 400, "expected business error")
        return exc.code
    raise AssertionError("expected request to fail")


def records(payload):
    if isinstance(payload, dict):
        return payload.get("records") or payload.get("data", {}).get("records") or []
    return []


def find_available_slot(departments):
    noons = ["MORNING", "AFTERNOON"]
    for offset in range(0, 7):
        visit_date = (date.today() + timedelta(days=offset)).isoformat()
        for dept in departments:
            dept_id = dept.get("deptId")
            if not dept_id:
                continue
            for noon in noons:
                payload = request(
                    "GET",
                    "/patient/doctors",
                    query={
                        "deptId": dept_id,
                        "visitDate": visit_date,
                        "noon": noon,
                        "pageNum": 1,
                        "pageSize": 50,
                    },
                )
                for doctor in records(payload):
                    if (doctor.get("remainingQuota") or 0) > 0:
                        return dept, doctor, visit_date, noon
    raise AssertionError("no available outpatient slot in next 7 days")


def main():
    admin = request("POST", "/auth/login", {"username": "admin", "password": "123456", "loginType": "ADMIN"})
    doctor_login = request("POST", "/auth/login", {"username": "doctor", "password": "123456", "loginType": "DOCTOR"})
    expect(admin.get("roleType") == "ADMIN", "admin login role mismatch")
    expect(doctor_login.get("roleType") == "DOCTOR", "doctor login role mismatch")

    departments = request("GET", "/patient/department/list")
    expect(isinstance(departments, list) and departments, "department list is empty")
    dept_keys = [item.get("deptId") for item in departments]
    dept_names = [item.get("deptName") for item in departments]
    expect(len(dept_keys) == len(set(dept_keys)), "department list contains duplicated deptId")
    expect(len(dept_names) == len(set(dept_names)), "department list contains duplicated deptName")
    dev_markers = ("Extended", "User Logic", "项目验收", "验收", "测试")
    expect(
        not any(any(marker in (name or "") for marker in dev_markers) for name in dept_names),
        "department list exposes development or acceptance test data",
    )

    dept, doctor, visit_date, noon = find_available_slot(departments)
    before_remaining = doctor.get("remainingQuota") or 0
    doctor_id = doctor["doctorId"]
    expect(doctor.get("specialty"), "doctor source does not expose real specialty text")

    generated_date = (date.today() + timedelta(days=2)).isoformat()
    generated = request(
        "POST",
        "/ai/schedule/generate",
        {
            "deptId": dept["deptId"],
            "startDate": generated_date,
            "endDate": generated_date,
            "ruleConfig": "验收：AI排班结果需要同步为患者可预约号源",
        },
    )
    generated_days = generated.get("results") or []
    expect(generated_days, "AI schedule generation returned no results")
    generated_shift = (generated_days[0].get("morning") or generated_days[0].get("afternoon") or [None])[0]
    expect(generated_shift, "AI schedule generation returned no doctor shift")
    generated_noon = "MORNING" if generated_days[0].get("morning") else "AFTERNOON"
    generated_doctors = request(
        "GET",
        "/patient/doctors",
        query={
            "deptId": dept["deptId"],
            "visitDate": generated_date,
            "noon": generated_noon,
            "pageNum": 1,
            "pageSize": 50,
        },
    )
    expect(
        any(item.get("doctorId") == generated_shift.get("employeeId") for item in records(generated_doctors)),
        "AI generated schedule is not visible as patient appointment source",
    )
    generated_doctor = next(item for item in records(generated_doctors) if item.get("doctorId") == generated_shift.get("employeeId"))
    expect(generated_doctor.get("specialty"), "AI generated patient-visible doctor has no specialty text")
    generated_history = request(
        "GET",
        "/ai/schedule/result",
        query={
            "deptId": dept["deptId"],
            "startDate": generated_date,
            "endDate": generated_date,
            "pageNum": 1,
            "pageSize": 50,
        },
    )
    expect(
        any(item.get("doctorId") == generated_shift.get("employeeId") for item in records(generated_history)),
        "AI schedule history query did not return generated result",
    )

    rand = random.randint(100, 999)
    now_tail = str(int(time.time()))[-4:]
    phone = "138" + str(random.randint(10000000, 99999999))
    card = f"1101011990{random.randint(1, 12):02d}{random.randint(1, 28):02d}{rand}X"
    patient_name = f"验收患者{now_tail}"

    register_body = {
        "realName": patient_name,
        "gender": "M",
        "cardNumber": card,
        "birthdate": "1990-01-01",
        "homeAddress": "端到端验收地址",
        "phone": phone,
        "deptId": dept["deptId"],
        "doctorId": doctor_id,
        "visitDate": visit_date,
        "noon": noon,
        "registLevelId": 1,
        "settleCategoryId": 1,
        "registMethod": "MOBILE",
    }
    register_id = request("POST", "/patient/register", register_body)
    expect(isinstance(register_id, int), "register endpoint did not return register id")

    after = request(
        "GET",
        "/patient/doctors",
        query={
            "deptId": dept["deptId"],
            "visitDate": visit_date,
            "noon": noon,
            "pageNum": 1,
            "pageSize": 50,
        },
    )
    after_doctor = next(item for item in records(after) if item.get("doctorId") == doctor_id)
    expect(after_doctor.get("remainingQuota") == before_remaining - 1, "remaining quota did not decrease after registration")

    expect_http_error("POST", "/patient/register", register_body)

    patients = request("GET", "/patient/list")
    patient = next((item for item in patients if item.get("phone") == phone), None)
    expect(patient and patient.get("patientId"), "new patient not visible in patient list")

    patient_records = request(
        "GET",
        "/patient/records",
        query={"patientId": patient["patientId"], "pageNum": 1, "pageSize": 20},
    )
    expect(any(item.get("registerId") == register_id for item in records(patient_records)), "patient records do not include new registration")

    doctor_queue = request(
        "GET",
        "/doctor/patients",
        query={
            "doctorId": doctor_id,
            "visitState": "REGISTERED",
            "visitDate": visit_date,
            "noon": noon,
            "pageNum": 1,
            "pageSize": 50,
        },
    )
    expect(any(item.get("registerId") == register_id for item in records(doctor_queue)), "doctor queue does not include patient registration")
    request("PUT", f"/doctor/patients/{register_id}/receive")
    received_queue = request(
        "GET",
        "/doctor/patients",
        query={
            "doctorId": doctor_id,
            "visitState": "DOCTOR_RECEIVED",
            "visitDate": visit_date,
            "noon": noon,
            "pageNum": 1,
            "pageSize": 50,
        },
    )
    expect(any(item.get("registerId") == register_id for item in records(received_queue)), "received patient is not visible in consulting queue")
    request("PUT", f"/doctor/patients/{register_id}/return-waiting")
    returned_queue = request(
        "GET",
        "/doctor/patients",
        query={
            "doctorId": doctor_id,
            "visitState": "REGISTERED",
            "visitDate": visit_date,
            "noon": noon,
            "pageNum": 1,
            "pageSize": 50,
        },
    )
    expect(any(item.get("registerId") == register_id for item in records(returned_queue)), "returned patient is not visible in waiting queue")

    check_catalog = request("GET", "/patient/medical-technology/check")
    if check_catalog:
        request(
            "POST",
            "/patient/check-request",
            {
                "patientId": patient["patientId"],
                "registerId": register_id,
                "medicalTechnologyIds": [check_catalog[0]["techId"]],
            },
        )
        check_requests = request(
            "GET",
            "/patient/check-requests",
            query={"patientId": patient["patientId"], "pageNum": 1, "pageSize": 20},
        )
        expect(records(check_requests), "check request was not created")

    inspection_catalog = request("GET", "/patient/medical-technology/inspection")
    if inspection_catalog:
        request(
            "POST",
            "/patient/inspection-request",
            {
                "patientId": patient["patientId"],
                "registerId": register_id,
                "medicalTechnologyIds": [inspection_catalog[0]["techId"]],
            },
        )
        inspection_requests = request(
            "GET",
            "/patient/inspection-requests",
            query={"patientId": patient["patientId"], "pageNum": 1, "pageSize": 20},
        )
        expect(records(inspection_requests), "inspection request was not created")

    sources = request(
        "GET",
        "/schedule/sources",
        query={
            "doctorId": doctor_id,
            "deptId": dept["deptId"],
            "startDate": visit_date,
            "endDate": visit_date,
            "pageNum": 1,
            "pageSize": 20,
        },
    )
    expect(records(sources), "admin schedule source query did not return selected slot")

    triage_events = post_sse(
        "/ai/consultation/triage/stream",
        {
            "patientId": patient["patientId"],
            "symptoms": "突发头痛伴恶心，无明确发热，想确认应该挂哪个科室",
            "conversationId": f"acceptance-patient-{patient['patientId']}",
        },
    )
    delta_text = "".join((payload.get("text") or "") for event, payload in triage_events if event == "delta")
    final_payload = next((payload for event, payload in triage_events if event == "final"), None)
    final_data = (final_payload or {}).get("data") or {}
    expect(len(delta_text.strip()) >= 20, "AI triage stream did not return readable delta text")
    expect(final_data.get("diagnosisHint"), "AI triage final response has no diagnosisHint")
    expect(final_data.get("recommendations"), "AI triage final response has no recommendations")

    print(json.dumps({
        "status": "PASS",
        "registerId": register_id,
        "patientId": patient["patientId"],
        "doctorId": doctor_id,
        "dept": dept.get("deptName"),
        "visitDate": visit_date,
        "noon": noon,
        "remainingBefore": before_remaining,
        "remainingAfter": after_doctor.get("remainingQuota"),
        "aiScheduleVisibleDate": generated_date,
        "aiScheduleDoctorId": generated_shift.get("employeeId"),
        "doctorReceiveAndReturn": True,
        "checkCatalog": len(check_catalog or []),
        "inspectionCatalog": len(inspection_catalog or []),
        "aiDeltaChars": len(delta_text.strip()),
        "aiRecommendationCount": len(final_data.get("recommendations") or []),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise
