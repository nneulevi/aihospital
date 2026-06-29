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
    stamp = int(time.time())
    patient_id = 990030000 + stamp
    common = {
        "role_scope": "patient",
        "user_id": "patient:semantic-check",
        "patient_id": patient_id,
        "memory_enabled": True,
    }
    old_conversation = f"patient:semantic-check:{stamp}:old"
    new_conversation = f"patient:semantic-check:{stamp}:new"
    post(
        {
            **common,
            "conversation_id": old_conversation,
            "symptoms": "Previous visit: I take warfarin every night after atrial fibrillation treatment.",
        }
    )
    result = post(
        {
            **common,
            "conversation_id": new_conversation,
            "symptoms": "Do you remember the anticoagulant medicine I mentioned earlier?",
        }
    )
    memory_context = result.get("memory_context", {})
    semantic_memories = memory_context.get("semantic_memories") or []
    output = {
        "status": "success",
        "old_conversation": old_conversation,
        "new_conversation": new_conversation,
        "patient_id": patient_id,
        "recent_message_count": memory_context.get("recent_message_count"),
        "semantic_result_count": memory_context.get("semantic_recall", {}).get("result_count"),
        "semantic_contents": [item.get("content") for item in semantic_memories[:3]],
    }
    print(json.dumps(output, ensure_ascii=True, indent=2))
    if output["recent_message_count"] != 0:
        return 1
    if not any("warfarin" in str(item.get("content", "")).lower() for item in semantic_memories):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
