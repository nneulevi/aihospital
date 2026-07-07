import json
import sys
import urllib.parse
import urllib.request


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


def records(payload):
    if isinstance(payload, dict):
        return payload.get("records") or payload.get("data", {}).get("records") or []
    return []


def expect(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def demo_pharmacist_id() -> int:
    payload = request(
        "POST",
        "/auth/login",
        {"username": "pharmacist", "password": "123456", "loginType": "PHARMACIST"},
    )
    employee_id = payload.get("employeeId") if isinstance(payload, dict) else None
    expect(employee_id is not None, f"pharmacist demo login did not return employeeId: {payload}")
    return int(employee_id)


def main():
    pharmacist_id = demo_pharmacist_id()
    inventory = request("GET", "/drugstore/inventory", query={"pageNum": 1, "pageSize": 20})
    drugs = records(inventory)
    expect(drugs, "drug inventory is empty")
    dev_markers = ("Extended", "User Logic", "BIZFLOW", "业务联动", "项目验收", "验收", "测试")
    exposed = [
        item.get("drugName")
        for item in drugs
        if any(marker in (item.get("drugName") or "") for marker in dev_markers)
        or any(marker in (item.get("manufacturer") or "") for marker in dev_markers)
        or str(item.get("drugCode") or "").startswith(("EXT-", "BIZFLOW-"))
    ]
    expect(not exposed, f"drug inventory exposes development or acceptance test data: {exposed[:5]}")
    drug = next((item for item in drugs if item.get("drugId") and item.get("drugName")), None)
    expect(drug, "drug inventory has no usable drug item")

    required_fields = ["drugId", "drugCode", "drugName", "drugFormat", "drugUnit", "stockNum", "drugPrice", "manufacturer"]
    missing_fields = [field for field in required_fields if drug.get(field) in (None, "")]
    expect(not missing_fields, f"drug inventory field mismatch: {missing_fields}")

    drug_id = drug["drugId"]
    before = int(drug.get("stockNum") or 0)
    request(
        "POST",
        "/drugstore/stock/in",
        {"drugId": drug_id, "quantity": 1, "operatorId": pharmacist_id, "reason": "端到端库存联动入库"},
    )
    after_in = request("GET", "/drugstore/inventory", query={"pageNum": 1, "pageSize": 50})
    updated = next(item for item in records(after_in) if item.get("drugId") == drug_id)
    expect(int(updated.get("stockNum") or 0) == before + 1, "stock did not increase after stock-in")

    stock_records = request("GET", "/drugstore/stock/records", query={"drugId": drug_id, "recordType": "IN", "pageNum": 1, "pageSize": 20})
    expect(any(item.get("afterStock") == before + 1 for item in records(stock_records)), "stock-in record not found")

    request(
        "POST",
        "/drugstore/stock/check",
        {"drugId": drug_id, "actualStock": before, "operatorId": pharmacist_id, "reason": "端到端库存联动恢复"},
    )
    restored_payload = request("GET", "/drugstore/inventory", query={"pageNum": 1, "pageSize": 50})
    restored = next(item for item in records(restored_payload) if item.get("drugId") == drug_id)
    expect(int(restored.get("stockNum") or 0) == before, "stock did not restore after stock-check")

    print(json.dumps({
        "status": "PASS",
        "drugId": drug_id,
        "drugName": drug.get("drugName"),
        "pharmacistId": pharmacist_id,
        "stockBefore": before,
        "stockAfterIn": before + 1,
        "stockRestored": before,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise
