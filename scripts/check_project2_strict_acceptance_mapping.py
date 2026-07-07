"""Strict Project2 frontend/backend acceptance mapping checks.

This script enforces the acceptance rule from `统一验收标准.md`:
frontend data must be based on matching backend business APIs, not unrelated
generic fallbacks.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"
BACKEND_CONTROLLERS = ROOT / "Project2" / "src" / "main" / "java" / "com" / "neuedu" / "his" / "controller"


REQUIRED_FRONTEND_SNIPPETS = {
    "patient departments API": "/patient/department/list",
    "patient today register API": "/patient/register/today",
    "patient check-in submit API": "/patient/checkin/submit",
    "patient queue status API": "/patient/queue/status",
    "patient inspection catalog API": "/patient/medical-technology/inspection",
    "patient check catalog API": "/patient/medical-technology/check",
    "patient inspection requests API": "/patient/inspection-requests",
    "patient check requests API": "/patient/check-requests",
    "patient prescriptions API": "/patient/prescriptions",
    "patient reports API": "/patient/reports",
    "patient queue departments API": "/patient/queue/depts",
    "patient queue count API": "/patient/queue/count",
    "patient self check request API": "/patient/check-request",
    "patient self inspection request API": "/patient/inspection-request",
    "patient prescription detail API": "/patient/prescriptions/",
    "patient report detail API": "/patient/reports/",
    "doctor profile API": "/doctor/profile",
    "doctor statistics API": "/doctor/statistics",
    "doctor check result detail API": "/doctor/check-result/",
    "admin pending charge items API": "/admin/finance/pending-items",
    "admin paid charge items API": "/admin/finance/paid-items",
    "admin pending dispense API": "/admin/drug/pending-dispense",
    "admin pending refund API": "/admin/drug/pending-refund",
    "admin employees API": "/admin/employee/list",
    "admin doctors API": "/admin/employee/doctors",
    "admin departments API": "/admin/department/list",
}

REQUIRED_BACKEND_SNIPPETS = {
    "patient departments endpoint": '@GetMapping("/department/list")',
    "patient today register endpoint": '@GetMapping("/register/today")',
    "patient check-in endpoint": '@PostMapping("/checkin/submit")',
    "patient queue status endpoint": '@GetMapping("/queue/status")',
    "patient inspection catalog endpoint": '@GetMapping("/medical-technology/inspection")',
    "patient check catalog endpoint": '@GetMapping("/medical-technology/check")',
    "patient inspection requests endpoint": '@GetMapping("/inspection-requests")',
    "patient check requests endpoint": '@GetMapping("/check-requests")',
    "patient prescriptions endpoint": '@GetMapping("/prescriptions")',
    "patient reports endpoint": '@GetMapping("/reports")',
    "patient queue departments endpoint": '@GetMapping("/queue/depts")',
    "patient queue count endpoint": '@GetMapping("/queue/count")',
    "patient self check request endpoint": '@PostMapping("/check-request")',
    "patient self inspection request endpoint": '@PostMapping("/inspection-request")',
    "patient prescription detail endpoint": '@GetMapping("/prescriptions/{id}")',
    "patient report detail endpoint": '@GetMapping("/reports/{id}")',
    "patient current endpoint": '@GetMapping("/current")',
    "patient book inspection endpoint": '@PutMapping("/inspection-request/book")',
    "patient book check endpoint": '@PutMapping("/check-request/book")',
    "doctor profile endpoint": '@GetMapping("/profile")',
    "doctor statistics endpoint": '@GetMapping("/statistics")',
    "doctor check result detail endpoint": '@GetMapping("/check-result/{id}")',
    "admin employee create endpoint": '@PostMapping("/employee/create")',
    "admin employees endpoint": '@GetMapping("/employee/list")',
    "admin doctors endpoint": '@GetMapping("/employee/doctors")',
    "admin departments endpoint": '@GetMapping("/department/list")',
    "admin doctor statistics endpoint": '@GetMapping("/statistics/doctor")',
    "admin department statistics endpoint": '@GetMapping("/statistics/dept")',
    "admin pending charge items endpoint": '@GetMapping("/finance/pending-items")',
    "admin paid charge items endpoint": '@GetMapping("/finance/paid-items")',
    "admin pending dispense endpoint": '@GetMapping("/drug/pending-dispense")',
    "admin pending refund endpoint": '@GetMapping("/drug/pending-refund")',
}

FORBIDDEN_FRONTEND_SNIPPETS = {
    "visible unfinished marker": "功能开发中",
    "hard-coded doctor name": "张医生",
    "hard-coded doctor visit metric": ">156<",
    "hard-coded doctor accuracy metric": "98%",
    "hard-coded patient rating metric": "4.9",
    "mock status leak": "mock_demo_only",
    "demo status leak": "模拟演示",
    "developer integration hint": "后续可接入",
}

FORBIDDEN_PAGE_SNIPPETS = {
    "Reports.vue must not reuse patient records": ("frontend/src/views/patient/Reports.vue", "getRecords"),
    "Prescriptions.vue must not reuse patient orders": ("frontend/src/views/patient/Prescriptions.vue", "getOrders"),
    "Checkin.vue must not use dashboard summary as check-in state": (
        "frontend/src/views/patient/Checkin.vue",
        "getPatientDashboardSummary",
    ),
    "QueueQuery.vue must not use dashboard summary as queue state": (
        "frontend/src/views/patient/QueueQuery.vue",
        "getPatientDashboardSummary",
    ),
}


def read_all_source(root: Path) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*")
        if path.suffix in {".java", ".ts", ".vue"}
    )


def main() -> None:
    frontend_source = read_all_source(FRONTEND)
    backend_source = read_all_source(BACKEND_CONTROLLERS)

    failures: list[str] = []
    for name, snippet in REQUIRED_FRONTEND_SNIPPETS.items():
        if snippet not in frontend_source:
            failures.append(f"missing frontend mapping: {name} -> {snippet}")

    for name, snippet in REQUIRED_BACKEND_SNIPPETS.items():
        if snippet not in backend_source:
            failures.append(f"missing backend endpoint: {name} -> {snippet}")

    for name, snippet in FORBIDDEN_FRONTEND_SNIPPETS.items():
        if snippet in frontend_source:
            failures.append(f"user-visible/developer snippet remains: {name} -> {snippet}")

    for name, (relative_path, snippet) in FORBIDDEN_PAGE_SNIPPETS.items():
        source = (ROOT / relative_path).read_text(encoding="utf-8", errors="ignore")
        if snippet in source:
            failures.append(f"degraded page data source: {name} contains {snippet}")

    if failures:
        raise SystemExit("Strict Project2 mapping check failed:\n- " + "\n- ".join(failures))

    print("Strict Project2 frontend/backend mapping check passed.")


if __name__ == "__main__":
    main()
