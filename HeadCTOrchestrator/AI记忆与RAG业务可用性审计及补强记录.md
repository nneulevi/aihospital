# AI 记忆与 RAG 业务可用性审计及补强记录

## 审计问题

本次围绕以下四点检查：

1. 是否存在“最小实现闭环但未达到实际业务场景”的部分。
2. 是否具备定期摘要压缩长上下文。
3. 是否真的有 AI 记忆，避免多轮对话突然忘记上文。
4. RAG 是否只有规范要求，缺少医学专业知识。

## 审计结论

### 1. 最小闭环但仍有实际业务风险的部分

存在。

当前主平台、Orchestrator、Report、EMR、RAG、LLM、AI 问诊和 AI 辅助诊断链路已经能稳定运行，但影像模型层仍有真实业务风险：

- 金属伪影分割仍依赖本地训练权重或 fallback，成熟公开分割 checkpoint 未完全补齐。
- 病灶识别接入了 VinBigData raw checkpoint，但项目仍需要持续校验架构兼容性、真实样本泛化能力和输出稳定性。
- 因此当前更适合作为课程项目/演示系统的稳定可用版本，而不是未经验证直接用于真实医院生产。

本次已补强后端记忆、RAG 专业知识和可追溯输出；模型层风险需要后续通过真实数据评估、成熟 checkpoint 替换和临床样本验证继续降低。

### 2. 定期摘要压缩长上下文

原实现存在滚动摘要，但缺少明确的“压缩进度”记录。

本次已补强：

- 新增 `SUMMARY_COMPRESSION_MESSAGE_INTERVAL=6`。
- 每轮保存原始用户消息和 AI 回复。
- 首轮和每累计 6 条未摘要消息触发摘要压缩。
- `memory_context.compression` 返回：
  - `strategy=rolling_structured_summary`
  - `summary_max_chars`
  - `recent_message_limit`
  - `compression_interval_messages`
  - `summarized_message_count`
  - `has_unsummarized_messages`

这样系统不再只是保存最近消息，而是具备“最近消息窗口 + 长期摘要 + 关键事实”的混合记忆。

### 3. AI 记忆能力

存在真实记忆功能，并已增强：

- 原始消息保存到 `conversation_messages`。
- 会话摘要、关键事实、未解决问题保存到 `conversation_sessions`。
- 同一 `conversation_id` 的下一轮请求会注入：
  - `summary`
  - `key_facts`
  - `unresolved_questions`
  - `recent_messages`
  - `compression`
- Project2 自动生成稳定会话 ID：
  - 问诊：`patient:{patientId}:consultation`
  - 诊断：`medical_record:{medicalRecordId}:diagnosis`

注意：AI 记忆不是 LLM 自己永久记住，而是后端保存、压缩、检索后重新喂给 LLM。只要调用方保持同一 `conversation_id`，系统就不会因为单次上下文窗口变短而完全丢失上文。

### 4. RAG 医学专业知识

原知识库已有报告规范、伪影规范、CQ500 标签说明和颅内出血报告表达，但医学专业知识厚度不够。

本次新增：

- `acute_head_ct_findings.md`
  - 急诊头部 CT 关键影像征象。
  - 覆盖颅内出血、脑梗死/缺血、颅骨外伤、脑室系统、脑积水和报告辅助表达。

- `intracranial_hemorrhage_subtypes.md`
  - 颅内出血亚型与 CT 影像要点。
  - 覆盖脑实质出血、蛛网膜下腔出血、硬膜下血肿、硬膜外血肿、脑室内出血。

重新入库后：

```json
{
  "status": "success",
  "document_count": 12,
  "chunk_count": 67
}
```

检索验证：

```text
query: 硬膜外血肿 双凸透镜样 颅缝 骨折 CT 复核
sources: ich_subtype_knowledge_v1, acute_head_ct_findings_v1
status: success
recall_count: 20
```

## 本次代码补强

### 记忆压缩

- `HeadCTOrchestrator/conversation/memory_service.py`
  - 增加 `message_count()`。
  - 增加 `summarized_message_count`。
  - 增加 `memory_context.compression`。
  - 增加周期性摘要压缩策略。

- `HeadCTOrchestrator/rag/schema.sql`
  - `conversation_sessions` 增加：
    - `summarized_message_count`
    - `last_summary_at`

### 医学知识库

- `HeadCTOrchestrator/rag/knowledge/acute_head_ct_findings.md`
- `HeadCTOrchestrator/rag/knowledge/intracranial_hemorrhage_subtypes.md`

### 测试

- `HeadCTOrchestrator/tests/test_conversation_memory.py`
  - 新增长期上下文压缩测试。

- `HeadCTOrchestrator/tests/test_rag_components.py`
  - 新增医学知识文档存在性检查。

## 验收证据

### 单元测试

```powershell
python -m pytest HeadCTOrchestrator/tests/test_conversation_memory.py HeadCTOrchestrator/tests/test_rag_components.py -q
```

结果：

```text
20 passed in 0.28s
```

### RAG 入库

```powershell
. D:\exam\HeadCTOrchestrator\scripts\headct_rag_env.local.ps1
python -m HeadCTOrchestrator.rag.ingest_knowledge
```

结果：

```json
{
  "status": "success",
  "document_count": 12,
  "chunk_count": 67
}
```

### 记忆链路

```powershell
python scripts\check_clinical_memory_flow.py
```

结果：

```json
{
  "status": "success",
  "first_recent": 0,
  "second_recent": 2,
  "key_facts": [
    "头痛持续3天",
    "伴恶心",
    "有高血压病史"
  ]
}
```

### 正常业务链路

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

## 后续仍建议推进

1. 对话关键事实 embedding 入 pgvector，实现跨长时间跨度语义召回。
2. 增加患者端/医生端的历史会话列表和对话详情展示。
3. 继续补充头部 CT 医学知识库：
   - 脑肿瘤/占位效应；
   - 脑积水；
   - 颅骨骨折；
   - 脑梗死早期 CT 征象；
   - 术后改变和常见伪影鉴别。
4. 继续解决影像模型真实权重和真实数据评估问题。
