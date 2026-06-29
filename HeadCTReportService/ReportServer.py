"""FastAPI entrypoint for AI-assisted medical report workflow."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    API_PREFIX,
    HOST,
    MODULE_NAME,
    MODULE_VERSION,
    PORT,
    REPORT_AUTO_INIT_DB,
    SERVICE_DIR,
)
from .db import Database
from .exceptions import ReportServiceError
from .repositories.report_repository import PostgresReportRepository
from .schemas import (
    Actor,
    AmendmentRequest,
    BindAnalysisRequest,
    CreateReportRequest,
    EditDraftRequest,
    RegisterExaminationRequest,
    ReviewDecisionRequest,
)
from .service_clients.emr_client import EmrClient
from .service_clients.orchestrator_client import OrchestratorClient
from .services.report_service import ReportService


database = Database()
repository = PostgresReportRepository(database)
orchestrator_client = OrchestratorClient()
emr_client = EmrClient()
service = ReportService(repository, orchestrator_client, emr_client)
FRONTEND_DIR = SERVICE_DIR / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if REPORT_AUTO_INIT_DB:
        database.initialize()
    yield


app = FastAPI(title="头部 CT AI 智能检查报告服务", version=MODULE_VERSION, lifespan=lifespan)


def actor_from_headers(
    x_actor_id: Optional[str] = Header(default=None, alias="X-Actor-Id"),
    x_actor_role: Optional[str] = Header(default=None, alias="X-Actor-Role"),
) -> dict[str, str]:
    if not x_actor_id or not x_actor_role:
        raise ReportServiceError("IDENTITY_REQUIRED", "缺少调用者身份请求头", 401)
    actor = Actor(actor_id=x_actor_id.strip(), role=x_actor_role.strip())
    if not actor.actor_id or not actor.role:
        raise ReportServiceError("IDENTITY_REQUIRED", "缺少有效的调用者身份", 401)
    return actor.model_dump() if hasattr(actor, "model_dump") else actor.dict()


def request_audit(request: Request) -> dict[str, Optional[str]]:
    return {
        "request_id": request.headers.get("X-Request-Id") or uuid.uuid4().hex,
        "client_ip": request.client.host if request.client else None,
    }


def model_payload(model: Any) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


@app.exception_handler(ReportServiceError)
async def report_error_handler(_: Request, exc: ReportServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "REQUEST_VALIDATION_FAILED", "message": "请求参数校验失败", "details": {"errors": exc.errors()}}},
    )


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get(f"{API_PREFIX}/health")
async def health() -> dict[str, Any]:
    db_health = database.health()
    return {
        "status": "ok" if db_health.get("status") == "ok" else "degraded",
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "database": db_health,
        "orchestrator": orchestrator_client.health(),
        "emr": emr_client.health(),
    }


@app.post(f"{API_PREFIX}/integrations/examinations")
async def register_examination(
    payload: RegisterExaminationRequest,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    return {"status": "success", "examination": service.register_examination(model_payload(payload), actor)}


@app.post(f"{API_PREFIX}/integrations/examinations/{{study_id}}/analysis")
async def bind_analysis(
    study_id: str,
    payload: BindAnalysisRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    report = service.bind_analysis(
        study_id, payload.orchestrator_task_id, payload.assigned_doctor_id,
        actor, idempotency_key, **request_audit(request),
    )
    return {"status": "success", "report": report}


@app.post(f"{API_PREFIX}/reports/from-analysis/{{task_id}}")
async def create_report_from_analysis(
    task_id: str,
    payload: CreateReportRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    report = service.create_report_from_analysis(
        task_id=task_id,
        examination=model_payload(payload),
        actor=actor,
        idempotency_key=idempotency_key,
        **request_audit(request),
    )
    return {"status": "success", "report": report}


@app.get(f"{API_PREFIX}/reports")
async def list_reports(
    status: Optional[str] = None,
    doctor_id: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    reports = service.list_reports(actor, status=status, doctor_id=doctor_id, department=department, limit=limit)
    return {"status": "success", "reports": reports, "count": len(reports)}


@app.get(f"{API_PREFIX}/reports/{{report_id}}")
async def get_report(
    report_id: str,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    return {"status": "success", "report": service.get_report(report_id, actor)}


@app.get(f"{API_PREFIX}/reports/{{report_id}}/versions")
async def get_versions(
    report_id: str,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    service.get_report(report_id, actor)
    versions = repository.list_versions(report_id)
    return {"status": "success", "versions": versions}


@app.get(f"{API_PREFIX}/reports/{{report_id}}/audit-events")
async def get_audit_events(
    report_id: str,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    service.get_report(report_id, actor)
    return {"status": "success", "events": repository.list_audit_events(report_id)}


@app.get(f"{API_PREFIX}/reports/{{report_id}}/references")
async def get_references(
    report_id: str,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    report = service.get_report(report_id, actor)
    return {"status": "success", "references": report.get("rag_references_json") or []}


@app.patch(f"{API_PREFIX}/reports/{{report_id}}/draft")
async def edit_draft(
    report_id: str,
    payload: EditDraftRequest,
    request: Request,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    report = service.edit_report(report_id, model_payload(payload), actor, **request_audit(request))
    return {"status": "success", "report": report}


@app.post(f"{API_PREFIX}/reports/{{report_id}}/submit-review")
async def submit_review(
    report_id: str,
    request: Request,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    return {"status": "success", "report": service.submit_review(report_id, actor, **request_audit(request))}


@app.post(f"{API_PREFIX}/reports/{{report_id}}/approve")
async def approve(
    report_id: str,
    payload: ReviewDecisionRequest,
    request: Request,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    return {"status": "success", "report": service.approve(report_id, payload.comment, actor, **request_audit(request))}


@app.post(f"{API_PREFIX}/reports/{{report_id}}/request-revision")
async def request_revision(
    report_id: str,
    payload: ReviewDecisionRequest,
    request: Request,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    return {"status": "success", "report": service.request_revision(report_id, payload.comment, actor, **request_audit(request))}


@app.post(f"{API_PREFIX}/reports/{{report_id}}/sign")
async def sign(
    report_id: str,
    request: Request,
    signature_confirmation: Optional[str] = Header(default=None, alias="X-Signature-Confirmation"),
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    if not signature_confirmation or signature_confirmation.strip().lower() != "confirm":
        raise ReportServiceError("SIGNATURE_CONFIRMATION_REQUIRED", "签署操作需要再次确认", 401)
    return {"status": "success", "report": service.sign(report_id, actor, **request_audit(request))}


@app.post(f"{API_PREFIX}/reports/{{report_id}}/release")
async def release(
    report_id: str,
    request: Request,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    return {"status": "success", "report": service.release(report_id, actor, **request_audit(request))}


@app.post(f"{API_PREFIX}/reports/{{report_id}}/amendments")
async def amend(
    report_id: str,
    payload: AmendmentRequest,
    request: Request,
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    return {"status": "success", "report": service.amend(report_id, model_payload(payload), actor, **request_audit(request))}


@app.post(f"{API_PREFIX}/integrations/emr/dispatch")
async def dispatch_emr(
    limit: int = Query(default=20, ge=1, le=100),
    actor: dict[str, str] = Depends(actor_from_headers),
) -> dict[str, Any]:
    return {"status": "success", **service.dispatch_outbox(actor, limit)}


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("HeadCTReportService.ReportServer:app", host=HOST, port=PORT, reload=False)
