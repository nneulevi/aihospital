# 语义记忆召回与 CT 医学知识库扩充记录

## 目标

本阶段继续增强两部分：

1. 实现跨长时间跨度语义召回，避免历史对话被最近消息窗口挤出后无法被 AI 使用。
2. 继续补充头部 CT 医学知识库，让 RAG 不只检索规范要求，还能检索具体医学影像知识。

## 语义记忆实现

### 架构

在原有 `summary + key_facts + recent_messages` 之外，新增 `semantic_memories`：

```text
当前问题
 -> embedding
 -> conversation_vector_memories pgvector/HNSW 召回
 -> 按 conversation_id 或同 role_scope + patient_id 隔离
 -> 注入 memory_context.semantic_memories
 -> 进入 LLM Prompt
```

### 存储表

新增表：

- `conversation_vector_memories`

关键字段：

- `conversation_id`
- `role_scope`
- `patient_id`
- `visit_id`
- `medical_record_id`
- `sender`
- `content`
- `structured_payload`
- `importance_score`
- `embedding vector(1536)`

索引：

- `idx_conversation_vector_scope`
- `idx_conversation_vector_conversation`
- `idx_conversation_vector_embedding_hnsw`

### 召回范围

语义召回遵循隔离规则：

1. 优先召回同一 `conversation_id` 的历史。
2. 允许召回同一 `role_scope + patient_id` 的其他历史会话。
3. 不跨患者、不跨角色混用记忆。

### 内存测试实现

单元测试环境使用 `InMemoryConversationStore`，通过医学相关词扩展和词元重叠模拟语义召回，例如：

- `anticoagulant` 可召回 `warfarin`
- `contrast` 可召回 `allergy`

正式 PostgreSQL 运行环境使用 embedding + pgvector。

## CT 医学知识库扩充

本次新增 4 份知识文档：

1. `early_ischemic_stroke_ct.md`
   - 早期缺血性卒中 CT 征象；
   - 灰白质分界欠清、脑沟变浅、大脑中动脉高密度征。

2. `skull_fracture_trauma_ct.md`
   - 颅脑外伤与颅骨骨折；
   - 骨窗、凹陷性骨折、颅内积气、硬膜外/硬膜下血肿。

3. `hydrocephalus_mass_effect_ct.md`
   - 脑积水、占位效应、中线移位；
   - 脑室系统、第四脑室受压、脑疝风险提示。

4. `postoperative_artifact_ct.md`
   - 术后改变、金属植入物与伪影鉴别；
   - 钛板、术腔、金属伪影和病灶误判风险。

## 入库结果

重新 embedding 入库后：

```json
{
  "status": "success",
  "document_count": 16,
  "chunk_count": 84
}
```

## 验收结果

### 单元测试

命令：

```powershell
python -m pytest HeadCTOrchestrator/tests/test_conversation_memory.py -q
```

结果：

```text
6 passed
```

命令：

```powershell
python -m pytest HeadCTOrchestrator/tests/test_rag_components.py::test_rag_knowledge_documents_exist HeadCTOrchestrator/tests/test_rag_components.py::test_rag_load_knowledge_chunks -q
```

结果：

```text
2 passed
```

### 运行态语义记忆召回

命令：

```powershell
python scripts\check_clinical_semantic_memory_flow.py
```

结果摘要：

```json
{
  "status": "success",
  "recent_message_count": 0,
  "semantic_result_count": 2,
  "semantic_contents": [
    "Previous visit: I take warfarin every night after atrial fibrillation treatment."
  ]
}
```

说明：新会话没有最近消息，但能通过语义记忆召回同一患者旧会话中的 `warfarin` 用药信息。

### RAG 医学知识召回

命令：

```powershell
. D:\exam\HeadCTOrchestrator\scripts\headct_rag_env.local.ps1
python scripts\check_rag_medical_knowledge.py
```

结果：

```json
{
  "status": "success",
  "matched": true
}
```

覆盖召回：

- `early_ischemic_stroke_ct_v1`
- `skull_fracture_trauma_ct_v1`
- `hydrocephalus_mass_effect_ct_v1`
- `postoperative_artifact_ct_v1`

## 当前结论

长上下文记忆已从“摘要 + 最近消息”升级为“摘要 + 最近消息 + 跨会话语义召回”。RAG 知识库也从偏报告规范扩展到更具体的头部 CT 医学影像知识，可为报告辅助、AI 问诊、AI 辅助诊断提供更专业的上下文。
