# Dual Artifact Segmentation And MAR Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Head CT workflow so artifact segmentation and mature MAR checkpoint metadata can travel together through Filter, Orchestrator, LesionDetection, and report assist.

**Architecture:** Keep the existing U-Net3D artifact segmentation contract as the source of mask/severity. Add a MAR correction channel that reports InDuDoNet checkpoint availability and, when an executable MAR engine is not available, returns an explicit non-corrected status instead of pretending a corrected CT was produced. Orchestrator passes this combined context to LesionDetection and report assist.

**Tech Stack:** Python, FastAPI, SimpleITK, PyTorch metadata validation, pytest/TestClient.

---

### Task 1: Extend Filter Contract With MAR Metadata

**Files:**
- Modify: `D:/exam/Filter/Fastapi/ct_artifact_contract.py`
- Modify: `D:/exam/Filter/Fastapi/CTDetectionServer.py`
- Test: `D:/exam/Filter/Fastapi/tests/test_ct_artifact_api.py`

- [ ] Write failing tests asserting Filter results contain `artifact_segmentation` and `artifact_reduction` blocks.
- [ ] Add a small MAR status builder that records checkpoint path, model name, task type, status, warning, and optional `corrected_ct_url`.
- [ ] Include the MAR block in `result.json` without changing the existing `download_url`, `mask_file`, or preview fields.
- [ ] Run `python -m pytest Filter/Fastapi/tests/test_ct_artifact_api.py -q`.

### Task 2: Pass Combined Quality Context Into LesionDetection

**Files:**
- Modify: `D:/exam/HeadCTOrchestrator/OrchestratorServer.py`
- Modify: `D:/exam/HeadCTOrchestrator/service_clients/lesion_client.py`
- Modify: `D:/exam/HeadCTLesionDetection/LesionDetectionServer.py`
- Test: `D:/exam/HeadCTOrchestrator/tests/test_orchestrator_pipeline.py`
- Test: `D:/exam/HeadCTLesionDetection/tests/test_lesion_contract.py`

- [ ] Write failing tests asserting Orchestrator result exposes `quality_control.artifact_reduction`.
- [ ] Write failing tests asserting Lesion result records `input_policy.used_input="original_ct"` when MAR is registered but no executable corrected CT exists.
- [ ] Add `artifact_reduction` to `build_quality_context`.
- [ ] Add `input_policy` to LesionDetection result based on `quality_context.artifact_reduction`.
- [ ] Run Orchestrator and Lesion tests.

### Task 3: Improve Report Assist Warnings

**Files:**
- Modify: `D:/exam/HeadCTOrchestrator/OrchestratorServer.py`
- Test: `D:/exam/HeadCTOrchestrator/tests/test_orchestrator_pipeline.py`

- [ ] Write failing test asserting report assist warnings mention that MAR checkpoint is registered but corrected CT was not used when no executable correction is available.
- [ ] Extend `combine_report_assist` to append MAR status warnings from lesion analysis or quality context.
- [ ] Keep prohibited claims and doctor-review requirement unchanged.

### Task 4: Documentation And Regression

**Files:**
- Modify: `D:/exam/Filter/model/README.md`
- Modify: `D:/exam/真实成熟Checkpoint接入记录.md`

- [ ] Document the dual-channel workflow and the current boundary: InDuDoNet checkpoint is registered for MAR, but executable correction requires upstream model code/projection preprocessing.
- [ ] Run `python scripts/validate_true_checkpoints.py --strict-mature`.
- [ ] Run `python -m pytest Filter/Fastapi/tests/test_ct_artifact_api.py HeadCTLesionDetection/tests/test_lesion_contract.py HeadCTOrchestrator/tests/test_orchestrator_pipeline.py -q`.
- [ ] Run `python scripts/smoke_test_headct_platform.py`.
