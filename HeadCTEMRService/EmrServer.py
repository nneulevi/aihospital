"""FastAPI service receiving finalized reports from HeadCTReportService."""

from __future__ import annotations

import hmac
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from .config import API_PREFIX, EMR_AUTO_INIT_DB, EMR_SERVICE_TOKEN, HOST, MODULE_NAME, MODULE_VERSION, PORT
from .db import Database
from .repository import EmrConflict, EmrRepository
from .schemas import DiagnosticReportInput


database = Database()
repository = EmrRepository(database)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if EMR_AUTO_INIT_DB:
        database.initialize()
    if not EMR_SERVICE_TOKEN:
        raise RuntimeError("EMR_SERVICE_TOKEN is not configured")
    yield


app = FastAPI(title="头部 CT 电子病历接收服务", version=MODULE_VERSION, lifespan=lifespan)


def authorize(authorization: Optional[str] = Header(default=None, alias="Authorization")) -> None:
    expected = f"Bearer {EMR_SERVICE_TOKEN}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="invalid service credential")


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "UNAUTHORIZED" if exc.status_code == 401 else f"HTTP_{exc.status_code}", "message": str(exc.detail)}},
    )


@app.get("/health")
@app.get(f"{API_PREFIX}/health")
async def health() -> dict[str, Any]:
    db_health = database.health()
    return {
        "status": "ok" if db_health.get("status") == "ok" and bool(EMR_SERVICE_TOKEN) else "degraded",
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "database": db_health,
        "authentication": "configured" if EMR_SERVICE_TOKEN else "not_configured",
    }


@app.post(f"{API_PREFIX}/diagnostic-reports", dependencies=[Depends(authorize)])
async def receive_diagnostic_report(
    payload: DiagnosticReportInput,
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> JSONResponse:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key is required")
    if payload.status != "released" or not payload.signed_by or not payload.signed_at:
        raise HTTPException(status_code=422, detail="only signed and released reports are accepted")
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    try:
        report, created = repository.create_or_get(
            data,
            idempotency_key,
            request_id or uuid.uuid4().hex,
            request.client.host if request.client else None,
        )
    except EmrConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return JSONResponse(
        status_code=201 if created else 200,
        content={
            "status": "success",
            "created": created,
            "document_id": report["document_id"],
            "source_report_id": str(report["source_report_id"]),
        },
    )


@app.get(f"{API_PREFIX}/diagnostic-reports", dependencies=[Depends(authorize)])
async def list_reports(
    patient_id: Optional[str] = None,
    study_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    rows = repository.list(patient_id, study_id, limit)
    return {"status": "success", "reports": rows, "count": len(rows)}


@app.get(f"{API_PREFIX}/diagnostic-reports/{{document_id}}", dependencies=[Depends(authorize)])
async def get_report(document_id: str) -> dict[str, Any]:
    row = repository.get(document_id)
    if not row:
        raise HTTPException(status_code=404, detail="diagnostic report not found")
    return {"status": "success", "report": row, "audit_events": repository.audit_events(document_id)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("HeadCTEMRService.EmrServer:app", host=HOST, port=PORT, reload=False)

