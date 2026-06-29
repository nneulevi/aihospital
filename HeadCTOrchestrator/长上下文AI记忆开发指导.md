# 长上下文 AI 记忆开发指导

## 1. 建设目标

医生端和患者端可能与 AI 进行多轮、长上下文对话。不能依赖 LLM 上下文窗口本身“记住”内容，必须由后端保存、摘要、检索并按角色隔离后再注入 Prompt。

本阶段目标是在不破坏现有 Project2、HeadCTOrchestrator、RAG/LLM 接口的前提下，为 AI 问诊和 AI 辅助诊断补充长上下文记忆能力。

## 2. 设计原则

1. **开闭原则**
   - 现有 `/api/head-ct-ai/clinical/consultation` 和 `/api/head-ct-ai/clinical/diagnosis` 请求仍可不带记忆字段。
   - 新增字段以扩展形式进入请求和响应，不改变旧字段语义。

2. **角色隔离**
   - 患者、医生、管理员使用不同 `role_scope`。
   - 记忆边界为 `role_scope + patient_id + visit_id/medical_record_id + conversation_id`。

3. **短期 + 长期 + 语义记忆**
   - 短期：保存最近多轮原始对话。
   - 长期：维护滚动摘要和未解决问题。
   - 语义：把关键片段保留为可检索文本，后续可接 pgvector embedding。

4. **业务安全**
   - AI 输出仍是辅助建议。
   - 医生内部审核信息不应注入患者端 Prompt。
   - 记忆上下文只作为 LLM 输入依据，不直接覆盖病历、报告或诊断。

## 3. 推荐数据结构

### conversation_sessions

保存对话会话元信息：

- `id`
- `conversation_id`
- `role_scope`
- `user_id`
- `patient_id`
- `visit_id`
- `medical_record_id`
- `scene`
- `summary`
- `key_facts`
- `unresolved_questions`
- `created_at`
- `updated_at`

### conversation_messages

保存原始消息：

- `id`
- `conversation_id`
- `sender`
- `content`
- `structured_payload`
- `importance_score`
- `created_at`

## 4. Prompt 组装策略

每次 AI 调用时按以下顺序构造上下文：

```text
System 安全规则
+ 当前角色与业务场景
+ 当前患者/就诊/病历结构化信息
+ 长期摘要 summary
+ 关键事实 key_facts
+ 未解决问题 unresolved_questions
+ 最近若干轮消息 recent_messages
+ RAG 医学知识召回内容
+ 当前问题
```

## 5. Orchestrator 接口扩展

请求可选增加：

```json
{
  "conversation_id": "patient-12-consultation",
  "user_id": "patient-12",
  "role_scope": "patient",
  "visit_id": 1001,
  "memory_enabled": true
}
```

响应新增：

```json
{
  "memory_context": {
    "enabled": true,
    "conversation_id": "...",
    "summary": "...",
    "key_facts": [],
    "recent_message_count": 3
  }
}
```

## 6. Project2 接入策略

Project2 Real AI 服务调用 Orchestrator 时自动生成稳定 `conversation_id`：

- AI 问诊：`patient:{patientId}:consultation`
- AI 辅助诊断：`medical_record:{medicalRecordId}:diagnosis`

这样前端无需立即改造，也能让同一患者/同一病历的多轮 AI 交互具备记忆。

## 7. 验收标准

1. 不带 `conversation_id` 的旧请求仍能正常工作。
2. 带 `conversation_id` 的请求会保存用户消息和 AI 消息。
3. 下一次同一 `conversation_id` 调用时，Prompt 中包含摘要、关键事实和最近消息。
4. 不同角色或不同患者的会话互相隔离。
5. RAG/LLM 单元测试通过。
6. Project2 正常业务端到端脚本通过。

## 8. 后续增强

1. 将关键消息 embedding 后写入 pgvector，实现跨长时间跨度语义召回。
2. 增加会话列表、会话详情接口，供前端展示历史 AI 对话。
3. 为患者端小程序和医生端 Web 分别定制不同记忆暴露范围。
4. 对摘要更新引入异步任务，避免高并发时阻塞主请求。
