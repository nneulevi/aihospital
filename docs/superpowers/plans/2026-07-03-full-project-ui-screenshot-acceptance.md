# Full Project UI Screenshot Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run screenshot-level acceptance covering every project UI route, standalone frontend, and scanned interaction point.

**Architecture:** Generate a route/interaction matrix from source, then drive Playwright through role-based real login sessions. Each route gets at least one screenshot, and each user-visible interaction gets either a clicked screenshot or an explicit non-triggerable note in the final report.

**Tech Stack:** Vue 3, Vite, Playwright, FastAPI static frontends, Markdown evidence reports.

---

### Task 1: Generate The Coverage Matrix

**Files:**
- Create: `scripts/generate_full_ui_interaction_inventory.py`
- Output: `全项目界面与交互覆盖矩阵_2026-07-03.md`

- [x] **Step 1: Scan router and standalone frontends**

Run:

```powershell
$env:PYTHONUTF8='1'
python -X utf8 scripts\generate_full_ui_interaction_inventory.py
```

Expected:

```text
routes=47
```

### Task 2: Add Full UI Playwright Acceptance

**Files:**
- Create: `frontend/tests/visual/full-project-ui-acceptance.spec.ts`
- Output screenshots: `frontend/visual-results/full-project-ui-acceptance/`
- Output report: `全项目所有界面交互截图验收报告_2026-07-03.md`

- [x] **Step 1: Cover route screenshots**

Use role-based login helpers for PATIENT, DOCTOR, ADMIN, MEDICAL_TECH, PHARMACIST and visit/click through all 47 routes.

- [x] **Step 2: Cover standalone frontends**

Capture and interact with:

```text
http://127.0.0.1:8030
http://127.0.0.1:8000
```

- [x] **Step 3: Check bad user-visible signals**

Fail on:

```text
Request failed
服务器内部错误
Internal Server Error
undefined
null
raw JSON shown to normal users
empty toast/message
```

### Task 3: Execute And Iterate

**Files:**
- Modify app code only when Playwright exposes a real user-visible issue.
- Update: `目前存在问题_修复验收记录_2026-07-03.md`

- [x] **Step 1: Start all services**

Run:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
.\scripts\start_headct_platform.ps1 -Restart
```

- [x] **Step 2: Run full UI acceptance**

Run:

```powershell
cd frontend
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
npx playwright test -c playwright.config.ts tests/visual/full-project-ui-acceptance.spec.ts --project=desktop-chrome
```

- [x] **Step 3: Run compile/build/logic checks**

Run:

```powershell
cd D:\exam\frontend
npm run type-check
npm run build-only
cd D:\exam
python -X utf8 scripts\e2e_user_logic_acceptance.py
```

### Task 4: Final Evidence

**Files:**
- Output: `全项目所有界面交互截图验收报告_2026-07-03.md`
- Output: `全项目界面与交互覆盖矩阵_2026-07-03.md`

- [x] **Step 1: Verify report references all route names and standalone frontends**

Run:

```powershell
python -X utf8 -c "from pathlib import Path; s=Path('全项目所有界面交互截图验收报告_2026-07-03.md').read_text(encoding='utf-8'); print(s.count('| PASS |'))"
```

- [x] **Step 2: Verify screenshots exist**

Run:

```powershell
Get-ChildItem frontend\visual-results\full-project-ui-acceptance -Recurse -Filter *.png | Measure-Object
```
