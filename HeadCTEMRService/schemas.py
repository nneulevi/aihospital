"""Input schema for finalized diagnostic reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DiagnosticReportInput(BaseModel):
    id: UUID
    order_id: str = Field(min_length=1, max_length=128)
    study_id: str = Field(min_length=1, max_length=128)
    accession_number: Optional[str] = Field(default=None, max_length=128)
    patient_id: str = Field(min_length=1, max_length=128)
    department: Optional[str] = Field(default=None, max_length=128)
    status: str
    findings: str = Field(min_length=1)
    impression: str = Field(min_length=1)
    recommendations: str = ""
    signed_by: str = Field(min_length=1, max_length=128)
    signed_at: datetime
    released_at: Optional[datetime] = None
    version_number: int = Field(ge=1)
    content_hash: str = Field(min_length=64, max_length=64)
    orchestrator_task_id: Optional[str] = None
    model_versions: dict[str, Any] = Field(default_factory=dict)

