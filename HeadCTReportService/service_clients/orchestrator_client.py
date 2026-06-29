"""Client for consuming completed HeadCTOrchestrator tasks."""

from __future__ import annotations

from typing import Any

import httpx

from ..config import ORCHESTRATOR_BASE_URL, ORCHESTRATOR_TIMEOUT_SECONDS
from ..exceptions import ReportServiceError


class OrchestratorClient:
    def get_completed_result(self, task_id: str) -> dict[str, Any]:
        try:
            with httpx.Client(base_url=ORCHESTRATOR_BASE_URL, timeout=ORCHESTRATOR_TIMEOUT_SECONDS) as client:
                task_response = client.get(f"/api/head-ct-ai/tasks/{task_id}")
                if task_response.status_code == 404:
                    raise ReportServiceError("ANALYSIS_TASK_NOT_FOUND", "AI 分析任务不存在", 404)
                task_response.raise_for_status()
                task = task_response.json()
                if task.get("status") != "success":
                    raise ReportServiceError(
                        "ANALYSIS_NOT_COMPLETED",
                        "仅允许使用成功完成的 AI 分析任务创建报告",
                        409,
                        {"task_status": task.get("status")},
                    )
                result_response = client.get(f"/api/head-ct-ai/results/{task_id}")
                result_response.raise_for_status()
                result = result_response.json()
        except ReportServiceError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise ReportServiceError("ORCHESTRATOR_UNAVAILABLE", f"无法读取 AI 分析结果: {exc}", 503) from exc
        if result.get("status") != "success" or result.get("task_id") != task_id:
            raise ReportServiceError("ANALYSIS_RESULT_INVALID", "AI 分析结果状态或 task_id 无效", 422)
        return result

    def health(self) -> dict[str, Any]:
        try:
            with httpx.Client(base_url=ORCHESTRATOR_BASE_URL, timeout=5) as client:
                response = client.get("/api/head-ct-ai/health")
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            return {"status": "unavailable", "error": str(exc)}

