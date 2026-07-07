from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_contains(path: Path, tokens: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    return missing


def main() -> int:
    failures: list[str] = []

    admin_layout = ROOT / "frontend/src/views/layouts/AdminBusinessLayout.vue"
    missing_admin = require_contains(
        admin_layout,
        [
            "goAdminHome",
            "handleLogout",
            "logout()",
            "router.replace('/admin')",
            "router.replace('/auth/login')",
        ],
    )
    if missing_admin:
        failures.append(f"Admin layout missing navigation/session controls: {missing_admin}")

    triage_page = ROOT / "frontend/src/views/doctor/AITriage.vue"
    missing_triage = require_contains(
        triage_page,
        [
            "conversationId",
            "messages",
            "sendMessage",
            "newConversation",
            "appendAssistantDelta",
            "triageStream(",
        ],
    )
    if missing_triage:
        failures.append(f"Doctor AI triage page is not conversational: {missing_triage}")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("Admin navigation and conversational triage guards passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
