"""HTTP client for the Filter CT artifact service."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import httpx


class FilterClient:
    def health(self) -> dict[str, Any]:
        raise NotImplementedError

    def create_task(self, file_path: Path, filename: str, content_type: Optional[str]) -> dict[str, Any]:
        raise NotImplementedError

    def get_task(self, task_url: str) -> dict[str, Any]:
        raise NotImplementedError

    def get_result(self, result_url: str) -> dict[str, Any]:
        raise NotImplementedError

    def absolute_url(self, url_or_path: Optional[str]) -> Optional[str]:
        raise NotImplementedError


class HttpFilterClient(FilterClient):
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
        return self._get_json("/api/ct-artifact/health")

    def create_task(self, file_path: Path, filename: str, content_type: Optional[str]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            with file_path.open("rb") as file_obj:
                response = client.post(
                    self.absolute_url("/api/ct-artifact/tasks"),
                    files={"file": (filename, file_obj, content_type or "application/octet-stream")},
                )
            response.raise_for_status()
            return response.json()

    def get_task(self, task_url: str) -> dict[str, Any]:
        return self._get_json(task_url)

    def get_result(self, result_url: str) -> dict[str, Any]:
        return self._get_json(result_url)
