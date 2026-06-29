"""Run a real local five-service Head CT platform smoke workflow."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CT = ROOT / "Filter" / "model" / "runs" / "config_visual_smoke" / "sample_ct_positive.nii.gz"
ORCHESTRATOR = "http://127.0.0.1:8010"
REPORT = "http://127.0.0.1:8030"
EMR = "http://127.0.0.1:8040"
EMR_TOKEN = "headct-local-emr-change-before-production"


def actor(actor_id: str, role: str) -> dict[str, str]:
    return {"X-Actor-Id": actor_id, "X-Actor-Role": role}


def require_ok(response: httpx.Response) -> dict:
    response.raise_for_status()
    return response.json()


def main() -> None:
    if not SAMPLE_CT.exists():
        raise FileNotFoundError(SAMPLE_CT)
    suffix = uuid.uuid4().hex[:10]
    patient_id = f"SMOKE-PATIENT-{suffix}"
    study_id = f"SMOKE-STUDY-{suffix}"
    order_id = f"SMOKE-ORDER-{suffix}"
    accession = f"SMOKE-ACC-{suffix}"

    with httpx.Client(timeout=180) as client:
        with SAMPLE_CT.open("rb") as file_obj:
            task = require_ok(
                client.post(
                    f"{ORCHESTRATOR}/api/head-ct-ai/tasks",
                    data={
                        "patient_id": patient_id,
                        "study_id": study_id,
                        "doctor_id": "doctor-reporting-001",
                    },
                    files={"file": (SAMPLE_CT.name, file_obj, "application/octet-stream")},
                )
            )
        task_id = task["task_id"]
        for _ in range(360):
            current = require_ok(client.get(f"{ORCHESTRATOR}{task['task_url']}"))
            if current["status"] in {"success", "failed"}:
                break
            time.sleep(0.5)
        else:
            raise TimeoutError("Orchestrator task did not finish")
        if current["status"] != "success":
            raise RuntimeError(f"Orchestrator failed: {current}")
        result = require_ok(client.get(f"{ORCHESTRATOR}{current['result_url']}"))
        ai_status = result.get("ai_imaging_status") or {}
        if ai_status.get("project_use_status") not in {"ready_for_project_demo", "degraded_for_project_demo"}:
            raise RuntimeError(f"AI imaging project status missing or invalid: {ai_status}")
        if not ai_status.get("quality_control_model") or not ai_status.get("lesion_model"):
            raise RuntimeError(f"AI imaging model status is incomplete: {ai_status}")

        report_response = require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/from-analysis/{task_id}",
                headers={**actor("doctor-reporting-001", "reporting_doctor"), "Idempotency-Key": f"smoke-{task_id}"},
                json={
                    "order_id": order_id,
                    "study_id": study_id,
                    "patient_id": patient_id,
                    "accession_number": accession,
                    "department": "急诊科",
                    "assigned_doctor_id": "doctor-reporting-001",
                },
            )
        )["report"]
        report_id = str(report_response["id"])

        edited = require_ok(
            client.patch(
                f"{REPORT}/api/v1/reports/{report_id}/draft",
                headers=actor("doctor-reporting-001", "reporting_doctor"),
                json={
                    "findings": report_response["findings"] + "\n医生已结合原始影像完成复核。",
                    "impression": report_response["impression"],
                    "recommendations": report_response["recommendations"],
                    "expected_version": report_response["version_lock"],
                    "change_reason": "五服务端到端烟雾测试医生复核",
                },
            )
        )["report"]
        require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/{report_id}/submit-review",
                headers=actor("doctor-reporting-001", "reporting_doctor"),
            )
        )
        require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/{report_id}/approve",
                headers=actor("doctor-reviewing-001", "reviewing_doctor"),
                json={"comment": "技术链路审核通过。"},
            )
        )
        require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/{report_id}/sign",
                headers={
                    **actor("doctor-signing-001", "signing_doctor"),
                    "X-Signature-Confirmation": "confirm",
                },
            )
        )
        require_ok(
            client.post(
                f"{REPORT}/api/v1/reports/{report_id}/release",
                headers=actor("doctor-signing-001", "signing_doctor"),
            )
        )
        dispatch = require_ok(
            client.post(
                f"{REPORT}/api/v1/integrations/emr/dispatch",
                headers=actor("emr-bridge", "integration_service"),
            )
        )
        final_report = require_ok(
            client.get(
                f"{REPORT}/api/v1/reports/{report_id}",
                headers=actor("doctor-reporting-001", "reporting_doctor"),
            )
        )["report"]
        document_id = final_report.get("external_document_id")
        if not document_id:
            raise RuntimeError(f"EMR dispatch did not return a document id: {dispatch}")
        emr_report = require_ok(
            client.get(
                f"{EMR}/api/v1/diagnostic-reports/{document_id}",
                headers={"Authorization": f"Bearer {EMR_TOKEN}"},
            )
        )["report"]

    summary = {
        "task_id": task_id,
        "orchestrator_status": result["status"],
        "filter_backend": result["quality_control"].get("backend"),
        "lesion_status": result["lesion_analysis"].get("status"),
        "ai_imaging_project_status": ai_status.get("project_use_status"),
        "ai_imaging_workflow_ready": ai_status.get("workflow_ready"),
        "ai_lesion_task_type": (ai_status.get("lesion_model") or {}).get("task_type"),
        "ai_artifact_reduction_status": (ai_status.get("artifact_reduction") or {}).get("status"),
        "rag_status": (result["report_assist"].get("rag_context") or {}).get("status"),
        "llm_status": (result["report_assist"].get("llm_context") or {}).get("status"),
        "report_id": report_id,
        "report_status": final_report["status"],
        "report_version": edited["version_number"],
        "emr_document_id": document_id,
        "emr_status": emr_report["status"],
        "patient_id": patient_id,
        "study_id": study_id,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
