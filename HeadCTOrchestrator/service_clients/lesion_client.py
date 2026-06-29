"""HTTP client for the Head CT lesion detection service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import httpx


class LesionClient:
    def health(self) -> dict[str, Any]:
        raise NotImplementedError

    def create_task(
        self,
        file_path: Path,
        filename: str,
        content_type: Optional[str],
        case_context: dict[str, Any],
        quality_context: dict[str, Any],
        requested_lesions: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def get_task(self, task_url: str) -> dict[str, Any]:
        raise NotImplementedError

    def get_result(self, result_url: str) -> dict[str, Any]:
        raise NotImplementedError

    def absolute_url(self, url_or_path: Optional[str]) -> Optional[str]:
        raise NotImplementedError


class HttpLesionClient(LesionClient):
    def __init__(self, base_url: str, timeout_seconds: float = 300.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def absolute_url(self, url_or_path: Optional[str]) -> Optional[str]:
        if not url_or_path:
            return url_or_path
        if url_or_path.startswith(("http://", "https://")):
            return url_or_path
        return urljoin(f"{self.base_url}/", url_or_path.lstrip("/"))

    def _get_json(self, url_or_path: str) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.absolute_url(url_or_path))
            response.raise_for_status()
            return response.json()

    def health(self) -> dict[str, Any]:
        return self._get_json("/api/head-ct-lesion/health")

    def create_task(
        self,
        file_path: Path,
        filename: str,
        content_type: Optional[str],
        case_context: dict[str, Any],
        quality_context: dict[str, Any],
        requested_lesions: str,
    ) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            with file_path.open("rb") as file_obj:
                response = client.post(
                    self.absolute_url("/api/head-ct-lesion/tasks"),
                    data={
                        "case_context": json.dumps(case_context, ensure_ascii=False),
                        "quality_context": json.dumps(quality_context, ensure_ascii=False),
                        "requested_lesions": requested_lesions,
                    },
                    files={"file": (filename, file_obj, content_type or "application/octet-stream")},
                )
            response.raise_for_status()
            return response.json()

    def get_task(self, task_url: str) -> dict[str, Any]:
        return self._get_json(task_url)

    def get_result(self, result_url: str) -> dict[str, Any]:
        return self._get_json(result_url)
