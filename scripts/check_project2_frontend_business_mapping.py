"""Check that Project2 backend business modules have frontend API and route mappings."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"


REQUIRED_SNIPPETS = {
    "medical tech route": "path: '/medical-tech'",
    "medical tech task API": "/medical-tech/tasks",
    "medical tech execute API": "/medical-tech/tasks/${itemType}/${itemId}/execute",
    "medical tech report API": "/medical-tech/tasks/${itemType}/${itemId}/report",
    "medical tech AI interpret API": "/medical-tech/tasks/${itemType}/${itemId}/ai-interpret",
    "drugstore role route": "path: '/drugstore'",
    "drugstore stock in API": "/drugstore/stock/in",
    "drugstore stock check API": "/drugstore/stock/check",
    "drugstore stock alerts API": "/drugstore/stock/alerts",
    "drugstore stock records API": "/drugstore/stock/records",
    "schedule source list API": "/schedule/sources",
    "schedule quota API": "/schedule/sources/${scheduleId}/quota",
    "schedule suspend API": "/schedule/sources/${scheduleId}/suspend",
    "schedule resume API": "/schedule/sources/${scheduleId}/resume",
    "medical tech login role": "MEDICAL_TECH",
    "pharmacist login role": "PHARMACIST",
}


def main() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in FRONTEND_SRC.rglob("*")
        if path.suffix in {".ts", ".vue"}
    )
    missing = [name for name, snippet in REQUIRED_SNIPPETS.items() if snippet not in source]
    if missing:
        raise SystemExit("Missing frontend mappings: " + ", ".join(missing))
    print("Project2 frontend business mapping check passed.")


if __name__ == "__main__":
    main()
