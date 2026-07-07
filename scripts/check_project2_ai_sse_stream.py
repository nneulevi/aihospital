from __future__ import annotations

import json
import sys
import time
import urllib.request


BASE = "http://127.0.0.1:8092"


def post_sse(path: str, payload: dict, timeout: int = 120) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream",
        },
    )
    events: list[dict] = []
    current_event = "message"
    current_data: list[str] = []
    started = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as response:
        for raw in response:
            if time.time() - started > timeout:
                raise TimeoutError(path)
            line = raw.decode("utf-8").rstrip("\n")
            if not line:
                if current_data:
                    text = "\n".join(current_data)
                    events.append({"event": current_event, "data": text})
                    if current_event == "final":
                        break
                current_event = "message"
                current_data = []
                continue
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:"):
                current_data.append(line[5:].strip())

    delta_text = "".join(event["data"] for event in events if event["event"] == "delta")
    final_events = [event for event in events if event["event"] == "final"]
    return {
        "path": path,
        "event_count": len(events),
        "event_names": [event["event"] for event in events],
        "delta_count": sum(1 for event in events if event["event"] == "delta"),
        "delta_chars": len(delta_text),
        "has_final": bool(final_events),
    }


def main() -> int:
    stamp = int(time.time())
    checks = [
        post_sse(
            "/api/ai/consultation/triage/stream",
            {
                "patientId": 127,
                "symptoms": f"患者头痛伴恶心，既往高血压，验收流式问诊 {stamp}",
            },
        ),
        post_sse(
            "/api/ai/diagnosis/suggest/stream",
            {
                "medicalRecordId": 900000 + stamp,
                "symptoms": "突发头痛、呕吐，头部 CT 提示可疑高密度灶",
                "history": "高血压病史十年",
                "physique": "神志清楚，右侧肢体肌力稍弱",
            },
        ),
    ]
    output = {"status": "success", "checks": checks}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    for item in checks:
        if not item["has_final"] or item["delta_count"] < 1 or item["delta_chars"] < 5:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
