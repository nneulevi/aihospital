# AI Clinical Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add streaming responses for AI consultation and AI diagnosis interactions while keeping image analysis as task-based upload/inference.

**Architecture:** Keep existing blocking JSON endpoints unchanged. Add SSE endpoints in Orchestrator and Project2 that emit progress events and a final structured payload. Frontend patient/mini-patient AI pages consume Project2 SSE with `fetch` + `ReadableStream` and fall back to existing POST if streaming fails.

**Tech Stack:** FastAPI `StreamingResponse`, Spring Boot `StreamingResponseBody`, Vue 3, Vant, TypeScript fetch streaming.

---

### Task 1: Add Orchestrator SSE endpoints

**Files:**
- Modify: `HeadCTOrchestrator/OrchestratorServer.py`

- [ ] **Step 1: Import SSE utilities**

Add `json`, `Iterable`, and `StreamingResponse`.

- [ ] **Step 2: Add event formatter**

Create `_sse_event(event: str, payload: dict[str, Any]) -> str` that returns `event: <name>\ndata: <json>\n\n`.

- [ ] **Step 3: Add stream generator**

Create `_clinical_stream(kind, payload)` that yields `memory_loaded`, `rag_retrieved`, `llm_generating`, and final result from `generate_consultation_assist` or `generate_diagnosis_assist`.

- [ ] **Step 4: Add endpoints**

Add:

```python
@app.post(f"{API_PREFIX}/clinical/consultation/stream")
async def stream_clinical_consultation(payload: dict[str, Any]):
    return StreamingResponse(_clinical_stream("consultation", payload), media_type="text/event-stream")

@app.post(f"{API_PREFIX}/clinical/diagnosis/stream")
async def stream_clinical_diagnosis(payload: dict[str, Any]):
    return StreamingResponse(_clinical_stream("diagnosis", payload), media_type="text/event-stream")
```

### Task 2: Add Project2 streaming endpoints

**Files:**
- Modify: `Project2/src/main/java/com/neuedu/his/controller/AiConsultationController.java`
- Modify: `Project2/src/main/java/com/neuedu/his/controller/AiDiagnosisController.java`

- [ ] **Step 1: Add SSE write helper**

Each controller gets helper methods to write:

```java
private void writeEvent(OutputStream out, String event, String data) throws IOException {
    out.write(("event: " + event + "\n").getBytes(StandardCharsets.UTF_8));
    out.write(("data: " + data + "\n\n").getBytes(StandardCharsets.UTF_8));
    out.flush();
}
```

- [ ] **Step 2: Add stream endpoints**

Add:

```java
@PostMapping(value = "/triage/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public StreamingResponseBody triageStream(@RequestBody @Valid ConsultationRequestDTO request)
```

and:

```java
@PostMapping(value = "/suggest/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public StreamingResponseBody suggestStream(@RequestBody @Valid DiagnosisSuggestRequestDTO request)
```

Each endpoint emits stage events, calls the existing service, emits `final`, and emits `error` on exception.

### Task 3: Add frontend stream client

**Files:**
- Create: `frontend/src/utils/sseJson.ts`
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: Implement fetch stream parser**

Create `postJsonSse(url, body, handlers)` that parses `event:` and `data:` blocks.

- [ ] **Step 2: Export stream helpers**

Add `triageStream` and `diagnosisSuggestStream` wrappers.

### Task 4: Update patient AI pages

**Files:**
- Modify: `frontend/src/views/patient/AIInquiry.vue`
- Modify: `frontend/src/views/mini-patient/AI.vue`

- [ ] **Step 1: Use stream endpoint first**

Call `triageStream` and update loading text/progress on stage events.

- [ ] **Step 2: Preserve fallback**

If streaming fails, use existing `triage` call.

### Task 5: Verification

**Files:**
- No new files required.

- [ ] **Step 1: Backend compile**

Run:

```powershell
cd Project2
.\mvnw.cmd -q -DskipTests compile "-Dmaven.repo.local=D:\exam\.m2\repository"
```

- [ ] **Step 2: Frontend type check**

Run:

```powershell
cd frontend
npm run type-check
```

- [ ] **Step 3: Endpoint smoke**

Use curl or PowerShell to verify `/api/ai/consultation/triage/stream` returns `text/event-stream` and contains a `final` event.

