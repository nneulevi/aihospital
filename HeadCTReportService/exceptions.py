"""Stable domain errors exposed by the report API."""

from __future__ import annotations

from typing import Any, Optional


class ReportServiceError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def not_found(code: str, message: str) -> ReportServiceError:
    return ReportServiceError(code, message, 404)


def conflict(code: str, message: str, **details: Any) -> ReportServiceError:
    return ReportServiceError(code, message, 409, details)


def forbidden(code: str, message: str) -> ReportServiceError:
    return ReportServiceError(code, message, 403)

