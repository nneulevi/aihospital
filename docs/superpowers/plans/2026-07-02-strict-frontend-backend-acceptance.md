# Strict Frontend Backend Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Project2 satisfy the documented acceptance rule that every frontend interface maps to backend data and visible patient pages do not use unrelated fallback data.

**Architecture:** Keep the current Project2 service structure and add patient-specific read APIs for reports, prescriptions, queue/check-in, departments, and medical technology requests. Update frontend API wrappers and patient pages to use those dedicated endpoints. Add an audit script that fails if the known degraded mappings return.

**Tech Stack:** Spring Boot, MyBatis, PostgreSQL, Vue 3, Vant, TypeScript, Python/httpx acceptance scripts.

---

### Task 1: Add Strict Mapping Audit

**Files:**
- Create: `scripts/check_project2_strict_acceptance_mapping.py`

- [ ] Create an audit that checks frontend source for required dedicated APIs and rejects report/prescription/check-in/queue pages that reuse generic records/orders/dashboard calls.

- [ ] Run: `python scripts/check_project2_strict_acceptance_mapping.py`
Expected before implementation: FAIL with degraded mapping messages.

### Task 2: Add Patient Business Endpoints

**Files:**
- Modify: `Project2/src/main/java/com/neuedu/his/controller/PatientController.java`
- Modify: `Project2/src/main/java/com/neuedu/his/service/PatientService.java`
- Modify: `Project2/src/main/java/com/neuedu/his/service/impl/PatientServiceImpl.java`
- Modify: `Project2/src/main/java/com/neuedu/his/mapper/RegisterMapper.java`
- Modify: `Project2/src/main/resources/mapper/RegisterMapper.xml`
- Create: patient VO classes under `Project2/src/main/java/com/neuedu/his/model/vo/`

- [ ] Add `GET /api/patient/department/list`.
- [ ] Add `GET /api/patient/register/today`.
- [ ] Add `POST /api/patient/checkin/submit`.
- [ ] Add `GET /api/patient/queue/status`.
- [ ] Add `GET /api/patient/medical-technology/inspection`.
- [ ] Add `GET /api/patient/medical-technology/check`.
- [ ] Add `GET /api/patient/inspection-requests`.
- [ ] Add `GET /api/patient/check-requests`.
- [ ] Add `GET /api/patient/prescriptions`.
- [ ] Add `GET /api/patient/reports`.

### Task 3: Update Patient Frontend Pages

**Files:**
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/views/patient/Appointment.vue`
- Modify: `frontend/src/views/mini-patient/Appointment.vue`
- Modify: `frontend/src/views/patient/Reports.vue`
- Modify: `frontend/src/views/patient/Prescriptions.vue`
- Modify: `frontend/src/views/patient/Checkin.vue`
- Modify: `frontend/src/views/patient/QueueQuery.vue`

- [ ] Replace static department lists with backend departments.
- [ ] Replace report page records reuse with `/patient/reports`.
- [ ] Replace prescription page order filtering with `/patient/prescriptions`.
- [ ] Replace dashboard summary substitutes in check-in and queue pages with dedicated APIs.

### Task 4: Update Acceptance Coverage

**Files:**
- Modify: `scripts/e2e_project2_core_business.py`
- Modify: `统一验收记录_2026-07-02.md`

- [ ] Extend E2E checks to call the new patient endpoints after doctor creates requests and prescriptions.
- [ ] Record the strict mapping fix and fresh verification commands.

### Task 5: Verification

- [ ] Run `python scripts/check_project2_strict_acceptance_mapping.py`.
- [ ] Run Project2 compile.
- [ ] Run frontend type-check.
- [ ] Run Project2 core and extended business E2E scripts.
- [ ] Run user-facing Playwright tests if services are running.
