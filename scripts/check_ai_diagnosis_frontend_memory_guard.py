from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AID_PAGE = ROOT / "frontend" / "src" / "views" / "doctor" / "AIDiagnosis.vue"


def main() -> None:
    text = AID_PAGE.read_text(encoding="utf-8")
    forbidden = ["medicalRecordId: 1", "medicalRecordId:1"]
    hits = [item for item in forbidden if item in text]
    if hits:
        raise SystemExit(f"standalone AI diagnosis page must not use fixed medicalRecordId: {hits}")
    required = ["standaloneConversationId", "conversationId"]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"standalone AI diagnosis page must send isolated conversation id; missing: {missing}")
    print("AI diagnosis frontend memory guard passed")


if __name__ == "__main__":
    main()
