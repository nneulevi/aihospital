"""Electronic medical record integration client."""

from __future__ import annotations

from typing import Any

import httpx

from ..config import EMR_BASE_URL, EMR_ENABLED, EMR_SERVICE_TOKEN, EMR_TIMEOUT_SECONDS


class EmrClient:
    @property
    def enabled(self) -> bool:
        return EMR_ENABLED and bool(EMR_BASE_URL) and bool(EMR_SERVICE_TOKEN)

    def push_report(self, payload: dict[str, Any], idempotency_key: str) -> str:
        if not self.enabled:
            raise RuntimeError("EMR integration is not configured")
        with httpx.Client(base_url=EMR_BASE_URL, timeout=EMR_TIMEOUT_SECONDS) as client:
            response = client.post(
                "/api/v1/diagnostic-reports",
                json=payload,
                headers={
                    "Idempotency-Key": idempotency_key,
                    "Authorization": f"Bearer {EMR_SERVICE_TOKEN}",
                },
            )
            response.raise_for_status()
            result = response.json()
        external_id = result.get("document_id") or result.get("id")
        if not external_id:
            raise RuntimeError("EMR response does not contain document_id")
        return str(external_id)

    def health(self) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "not_configured"}
        try:
            with httpx.Client(base_url=EMR_BASE_URL, timeout=5) as client:
                response = client.get("/api/v1/health")
                response.raise_for_status()
                return {"status": "ok", "response": response.json()}
        except Exception as exc:
            return {"status": "unavailable", "error": str(exc)}
