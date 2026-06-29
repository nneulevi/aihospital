# Mature Checkpoint Priority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prefer mature public model checkpoints when present, while keeping smoke checkpoints as safe fallback when mature weights are missing.

**Architecture:** Runtime configuration chooses checkpoints by provenance. External mature weights live under `external_weights`; local project-trained and smoke weights are marked as fallback and never reported as mature public checkpoints.

**Tech Stack:** PowerShell startup script, FastAPI health payloads, Python validation script, pytest smoke/e2e tests.

---

### Task 1: Checkpoint Selection Metadata

**Files:**
- Modify: `scripts/start_headct_platform.ps1`
- Modify: `Filter/Fastapi/CTDetectionServer.py`
- Modify: `HeadCTLesionDetection/config.py`
- Modify: `HeadCTLesionDetection/LesionDetectionServer.py`

- [ ] Define mature external candidate paths.
- [ ] Select mature VinBigData classification checkpoint only when present.
- [ ] Use smoke fallback when no mature checkpoint exists.
- [ ] Expose checkpoint provenance in health responses.

### Task 2: Validation Script

**Files:**
- Create: `scripts/validate_true_checkpoints.py`

- [ ] Validate mature public checkpoint readiness.
- [ ] Distinguish classification checkpoint, segmentation checkpoint, and smoke fallback.
- [ ] Return JSON suitable for documentation and CI-style checks.

### Task 3: Documentation and Regression

**Files:**
- Create: `真实成熟Checkpoint接入记录.md`
- Modify: `true_checkpoint.md`

- [ ] Record source policy and current readiness.
- [ ] Run unit/smoke/e2e tests to prove fallback does not break existing chain.
