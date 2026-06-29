# 长上下文 AI 记忆接入记录

## 本次目标

为医生/患者与 AI 的长上下文对话补充后端记忆能力，使 AI 问诊和 AI 辅助诊断不再只依赖单次请求文本，而能读取同一会话内的历史摘要、关键事实和最近消息。

## 已完成内容

### 1. 指导文档

- 新增 `HeadCTOrchestrator/长上下文AI记忆开发指导.md`
- 明确短期记忆、长期摘要、角色隔离、Prompt 组装和 Project2 接入策略。

### 2. Orchestrator 记忆模块

- 新增 `HeadCTOrchestrator/conversation/memory_service.py`
- 支持：
  - `InMemoryConversationStore`：单元测试和开发验证。
  - `PostgresConversationStore`：正式运行使用 PostgreSQL。
  - `build_memory_context()`：构造 Prompt 记忆上下文。
  - `persist_conversation_turn()`：保存用户消息、AI 消息、摘要、关键事实。

### 3. 数据库表

已在 `HeadCTOrchestrator/rag/schema.sql` 中新增：

- `conversation_sessions`
- `conversation_messages`

并已执行 schema 初始化，当前数据库表结构已创建。

### 4. 临床 AI 接入

- `HeadCTOrchestrator/rag/clinical_assist.py`
  - AI 问诊和 AI 辅助诊断调用 LLM 前注入 `conversation_memory`。
  - 调用完成后写入用户消息、AI 回复和滚动摘要。
  - 响应新增 `memory_context`，旧字段保持兼容。

### 5. Project2 接入

- `Project2/src/main/java/com/neuedu/his/service/impl/ConsultationServiceRealImpl.java`
  - 自动传入 `conversation_id=patient:{patientId}:consultation`
  - 自动传入 `role_scope=patient`

- `Project2/src/main/java/com/neuedu/his/service/impl/DiagnosisServiceRealImpl.java`
  - 自动传入 `conversation_id=medical_record:{medicalRecordId}:diagnosis`
  - 自动传入 `role_scope=doctor`
  - 诊断证据保存 `memory_context`

### 6. 验收脚本

- 新增 `scripts/check_clinical_memory_flow.py`
- 连续两轮调用 Orchestrator AI 问诊接口，验证第二轮读取第一轮摘要和关键事实。

## 验收结果

### Python 单元测试

命令：

```powershell
python -m pytest HeadCTOrchestrator/tests/test_conversation_memory.py HeadCTOrchestrator/tests/test_rag_components.py -q
```

结果：

```text
19 passed
```

### Project2 编译

命令：

```powershell
cmd /c mvnw.cmd -q -DskipTests "-Dmaven.repo.local=D:\exam\.m2\repository" compile
```

结果：编译通过。

### 数据库 schema 初始化

命令：

```powershell
. D:\exam\HeadCTOrchestrator\scripts\headct_rag_env.local.ps1
python -c "from HeadCTOrchestrator.rag.db import initialize_schema; initialize_schema(); print('conversation_schema_ready')"
```

结果：

```text
conversation_schema_ready
```

### 长上下文记忆链路

命令：

```powershell
python scripts\check_clinical_memory_flow.py
```

结果摘要：

```json
{
  "status": "success",
  "first_recent": 0,
  "second_recent": 2,
  "second_summary": "用户提到：头痛持续3天，伴恶心，有高血压病史。",
  "key_facts": [
    "头痛持续3天",
    "伴恶心",
    "有高血压病史"
  ]
}
```

### Project2 正常业务链路

命令：

```powershell
python scripts\e2e_project2_real_business.py
```

结果摘要：

```json
{
  "status": "success",
  "project2": "UP",
  "orchestrator": "ok",
  "report": "ok",
  "emr": "ok",
  "ai_imaging_workflow_ready": true,
  "report_service_status": "released",
  "emr_status": "final"
}
```

## 当前结论

长上下文 AI 记忆已接入 Orchestrator 与 Project2 Real AI 调用链。医生/患者同一会话的后续 AI 请求可以读取历史摘要、关键事实和最近对话；旧接口调用仍保持兼容。

后续建议继续扩展语义记忆：将关键对话片段 embedding 后写入 pgvector，通过 HNSW 召回跨较长时间跨度的历史信息。
