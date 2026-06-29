# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import time
import urllib.request


BASE_URL = "http://127.0.0.1:8010/api/head-ct-ai/clinical/consultation"


def post(payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    conversation_id = f"patient:memory-check:{int(time.time())}:consultation"
    common = {
        "conversation_id": conversation_id,
        "role_scope": "patient",
        "user_id": "patient:memory-check",
        "patient_id": 99002,
        "memory_enabled": True,
    }
    first_symptoms = "\u5934\u75db\u6301\u7eed3\u5929\uff0c\u4f34\u6076\u5fc3\uff0c\u6709\u9ad8\u8840\u538b\u75c5\u53f2\u3002"
    second_symptoms = "\u73b0\u5728\u5934\u75db\u6bd4\u65e9\u4e0a\u66f4\u660e\u663e\uff0c\u8fd8\u9700\u8981\u8865\u5145\u4ec0\u4e48\u4fe1\u606f\uff1f"
    first = post({**common, "symptoms": first_symptoms})
    second = post({**common, "symptoms": second_symptoms})
    result = {
        "status": "success",
        "conversation_id": conversation_id,
        "first_recent": first.get("memory_context", {}).get("recent_message_count"),
        "second_recent": second.get("memory_context", {}).get("recent_message_count"),
        "second_summary": second.get("memory_context", {}).get("summary"),
        "key_facts": second.get("memory_context", {}).get("key_facts"),
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if result["first_recent"] != 0 or result["second_recent"] != 2:
        return 1
    expected_headache = "\u5934\u75db\u6301\u7eed3\u5929"
    expected_hypertension = "\u9ad8\u8840\u538b\u75c5\u53f2"
    if expected_headache not in str(result["second_summary"]):
        return 1
    if not any(expected_hypertension in fact for fact in (result["key_facts"] or [])):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
