"""Request and identity schemas for the report service."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Actor(BaseModel):
    actor_id: str
    role: str


class CreateReportRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=128)
    study_id: str = Field(min_length=1, max_length=128)
    patient_id: str = Field(min_length=1, max_length=128)
    accession_number: Optional[str] = Field(default=None, max_length=128)
    patient_name: Optional[str] = Field(default=None, max_length=128)
    department: Optional[str] = Field(default=None, max_length=128)
    ordering_doctor_id: Optional[str] = Field(default=None, max_length=128)
    study_instance_uid: Optional[str] = Field(default=None, max_length=256)
    assigned_doctor_id: Optional[str] = Field(default=None, max_length=128)


class RegisterExaminationRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=128)
    study_id: str = Field(min_length=1, max_length=128)
    patient_id: str = Field(min_length=1, max_length=128)
    accession_number: Optional[str] = Field(default=None, max_length=128)
    patient_name: Optional[str] = Field(default=None, max_length=128)
    department: Optional[str] = Field(default=None, max_length=128)
    ordering_doctor_id: Optional[str] = Field(default=None, max_length=128)
    study_instance_uid: Optional[str] = Field(default=None, max_length=256)


class BindAnalysisRequest(BaseModel):
    orchestrator_task_id: str = Field(min_length=1, max_length=128)
    assigned_doctor_id: Optional[str] = Field(default=None, max_length=128)


class EditDraftRequest(BaseModel):
    findings: str = Field(min_length=1)
    impression: str = Field(min_length=1)
    recommendations: str = ""
    expected_version: int = Field(ge=1)
    change_reason: Optional[str] = Field(default=None, max_length=500)


class ReviewDecisionRequest(BaseModel):
    comment: Optional[str] = Field(default=None, max_length=2000)


class AmendmentRequest(BaseModel):
    findings: str = Field(min_length=1)
    impression: str = Field(min_length=1)
    recommendations: str = ""
    reason: str = Field(min_length=1, max_length=2000)

