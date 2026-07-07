import json
import os
import sys
from collections import Counter

import requests


BASE_URL = os.getenv("PROJECT2_BASE_URL", "http://127.0.0.1:8092")
DEV_MARKERS = ("User Logic", "Extended", "E2E", "项目验收", "验收", "测试")


def fail(message: str) -> None:
    print(message)
    sys.exit(1)


def load_catalog(path: str):
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    if not response.ok:
        fail(f"{path} failed: HTTP {response.status_code} {response.text[:500]}")
    return response.json()


def assert_catalog(path: str, expected_type: str) -> None:
    items = load_catalog(path)
    if not items:
        fail(f"{path} returned empty catalog")

    texts = json.dumps(items, ensure_ascii=False)
    for marker in DEV_MARKERS:
        if marker in texts:
            fail(f"{path} exposed development/test marker: {marker}")

    wrong_type = [item for item in items if item.get("techType") != expected_type]
    if wrong_type:
        fail(f"{path} returned wrong techType: {wrong_type[:3]}")

    keys = [
        (
            item.get("techName"),
            str(item.get("techPrice")),
            item.get("techType"),
        )
        for item in items
    ]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        fail(f"{path} returned duplicated patient-visible catalog items: {duplicates[:10]}")

    print(json.dumps({"path": path, "count": len(items), "items": items}, ensure_ascii=False, indent=2))


def main() -> None:
    assert_catalog("/api/patient/medical-technology/check", "CHECK")
    assert_catalog("/api/patient/medical-technology/inspection", "INSPECTION")


if __name__ == "__main__":
    main()
