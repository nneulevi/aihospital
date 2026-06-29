# 阶段 I：医生审核闭环与报告辅助接入详细指导

更新时间：2026-06-12

## 1. 阶段目标

阶段 I 的目标是在 Orchestrator 已能汇总质控和病灶识别结果后，增加医生审核闭环，并为报告辅助内容预留 RAG/LLM 增强接口，让 AI 结果从“算法输出”进入“医生可复核、可记录、可追溯、可解释引用”的工作流。并且明确，该部分的工作一定与下层和上层模块兼容，保证工作链路打通。

本阶段不追求自动生成最终诊断，而是提供：

- 结构化 `report_assist`。
- 可由 RAG 增强的专业报告辅助建议。
- 可追溯的知识来源引用。
- 医生审核记录。
- 医生是否采纳 AI 建议的记录。
- 医生修改意见。
- 审核状态查询。
- 审计日志。

核心原则：

```text
AI 结果只作为辅助参考，最终结论必须由医生审核。
RAG 只增强报告辅助表达和参考依据，不改变影像模型的原始判断。
```

## 1.1 RAG 的定位边界

阶段 I 文档只定义医生审核闭环和 `report_assist` 对接字段。RAG 的知识库、向量数据库、pgvector、检索流程、阿里百炼可选接入、安全检查和验收标准已拆分到：

```text
HeadCTOrchestrator/RAG报告辅助增强开发指导.md
```

本阶段只保留三条边界：

- RAG/LLM 不读取原始 CT。
- RAG/LLM 不修改 `quality_control`、`lesion_analysis` 原始字段。
- RAG/LLM 生成的内容必须保留医生复核提示。

## 2. 当前基础

Orchestrator 当前已输出：

```json
{
  "quality_control": {},
  "lesion_analysis": {},
  "report_assist": {
    "summary": "...",
    "quality_control_text": "...",
    "lesion_text": "...",
    "warnings": [],
    "can_enter_report": true
  }
}
```

阶段 I 要在此基础上新增：

```text
POST /api/head-ct-ai/reviews/{task_id}
GET  /api/head-ct-ai/reviews/{task_id}
```

可选后续扩展：

```text
GET  /api/head-ct-ai/reviews
PATCH /api/head-ct-ai/reviews/{task_id}
```

第一版只建议实现 `POST` 和 `GET`。

## 3. 推荐文件结构

建议在 `HeadCTOrchestrator` 中新增：

```text
HeadCTOrchestrator/
  review_store.py
  tests/
    test_orchestrator_reviews.py
```

保留现有：

```text
HeadCTOrchestrator/
  OrchestratorServer.py
  task_store.py
  API_CONTRACT.md
  SPRING_BOOT_CLIENT_EXAMPLE.md
```

原因：

- `task_store.py` 继续负责任务。
- `review_store.py` 单独负责医生审核。
- 后续若接数据库，替换 `review_store.py` 即可。
- RAG 模块按 `RAG报告辅助增强开发指导.md` 独立建设，医生审核闭环只消费 `report_assist` 输出。

## 4. 审核数据落盘设计

每个任务目录：

```text
HeadCTOrchestrator/orchestrator_outputs/{task_id}/
  task.json
  orchestrator_result.json
  review.json
  review_events.jsonl
```

说明：

- `review.json` 保存当前最新审核状态。
- `review_events.jsonl` 保存审核事件流水，一行一个 JSON。
- 不直接修改原始 `orchestrator_result.json`，避免 AI 原始输出被覆盖。

## 5. review.json 推荐结构

```json
{
  "task_id": "xxx",
  "review_status": "confirmed",
  "doctor_id": "doctor_001",
  "reviewed_at": "2026-06-12T10:30:00",
  "doctor_comment": "已结合原始影像复核。",
  "artifact_review": {
    "accepted": true,
    "severity_override": null,
    "comment": null
  },
  "lesion_review": {
    "accepted": true,
    "lesion_overrides": [],
    "comment": null
  },
  "report_review": {
    "ai_summary_used": true,
    "final_report_text": "医生最终报告文本。",
    "final_report_used": true
  },
  "safety": {
    "doctor_confirmed_ai_is_reference_only": true,
    "requires_follow_up": false
  },
  "source_result_url": "/api/head-ct-ai/results/xxx",
  "created_at": "2026-06-12T10:30:00",
  "updated_at": "2026-06-12T10:30:00"
}
```

## 6. 审核状态枚举

第一版建议：

```text
pending
confirmed
modified
rejected
needs_follow_up
```

含义：

| 状态 | 含义 |
| --- | --- |
| `pending` | 尚未审核 |
| `confirmed` | 医生确认 AI 辅助结论可作为报告草稿参考 |
| `modified` | 医生部分采纳，并进行了修改 |
| `rejected` | 医生不采纳 AI 辅助结论 |
| `needs_follow_up` | 需要进一步检查或复核 |

## 7. POST 请求设计

接口：

```text
POST /api/head-ct-ai/reviews/{task_id}
```

请求体：

```json
{
  "review_status": "modified",
  "doctor_id": "doctor_001",
  "doctor_comment": "伪影区域已复核，病灶提示未完全采纳。",
  "artifact_review": {
    "accepted": true,
    "severity_override": null,
    "comment": "质控结果符合阅片感受。"
  },
  "lesion_review": {
    "accepted": false,
    "lesion_overrides": [
      {
        "lesion_type": "intracranial_hemorrhage",
        "detected": false,
        "comment": "原始影像复核后未见明确出血。"
      }
    ],
    "comment": "模型提示仅作参考。"
  },
  "report_review": {
    "ai_summary_used": false,
    "final_report_text": "头颅 CT 平扫：未见明确急性颅内出血征象。请结合临床。",
    "final_report_used": true
  },
  "safety": {
    "doctor_confirmed_ai_is_reference_only": true,
    "requires_follow_up": false
  }
}
```

返回：

```json
{
  "status": "success",
  "review": {}
}
```

## 8. GET 响应设计

接口：

```text
GET /api/head-ct-ai/reviews/{task_id}
```

如果已审核：

```json
{
  "status": "success",
  "review": {}
}
```

如果任务存在但未审核：

```json
{
  "status": "success",
  "review": {
    "task_id": "xxx",
    "review_status": "pending"
  }
}
```

如果任务不存在：

```json
{
  "status": "failed",
  "error_code": "TASK_NOT_FOUND",
  "message": "任务不存在"
}
```

## 9. report_assist 增强建议

当前 `report_assist` 可以继续保持兼容，但建议扩展为支持 RAG 增强的结构：

```json
{
  "summary": "...",
  "quality_control_text": "...",
  "lesion_text": "...",
  "rag_enhanced": true,
  "suggested_report_sections": {
    "findings": [],
    "impression": [],
    "limitations": []
  },
  "recommended_actions": [],
  "rag_context": {
    "enabled": true,
    "status": "success",
    "retrieval_confidence": 0.82,
    "sources": [
      {
        "source_id": "artifact_quality_v1",
        "title": "金属伪影质控说明",
        "type": "project_guideline",
        "matched_terms": ["metal_artifact", "moderate"]
      }
    ]
  },
  "llm_context": {
    "enabled": false,
    "provider": "rule_template",
    "model": null,
    "status": "disabled",
    "prompt_version": "report_assist_v1",
    "fallback_reason": null
  },
  "warnings": [],
  "can_enter_report": true,
  "requires_doctor_review": true,
  "prohibited_claims": [
    "确诊",
    "排除",
    "无需复核",
    "自动完成诊断"
  ]
}
```

### 9.1 suggested_report_sections

建议结构：

```json
{
  "findings": [
    "存在轻度金属伪影，建议关注邻近区域。",
    "未见明确颅内出血征象，建议结合原始影像复核。"
  ],
  "impression": [
    "AI 辅助分析未提示明确颅内出血征象。"
  ],
  "limitations": [
    "AI 结果仅供辅助参考，最终结论需医生审核。"
  ]
}
```

### 9.2 recommended_actions

建议枚举：

```text
review_original_ct
review_artifact_area
compare_prior_study
consider_follow_up
manual_report_review
```

示例：

```json
[
  {
    "code": "review_original_ct",
    "text": "建议医生结合原始 CT 影像复核。"
  },
  {
    "code": "review_artifact_area",
    "text": "建议重点复核金属伪影邻近区域。"
  }
]
```

### 9.3 rag_context

`rag_context` 用于记录报告辅助内容的检索来源，方便医生和平台追溯。

推荐结构：

```json
{
  "enabled": true,
  "status": "success",
  "retrieval_confidence": 0.82,
  "query_terms": [
    "head_ct",
    "metal_artifact",
    "intracranial_hemorrhage",
    "limited_by_artifact"
  ],
  "sources": [
    {
      "source_id": "hemorrhage_reporting_v1",
      "title": "颅内出血报告辅助说明",
      "type": "report_template",
      "matched_terms": ["hemorrhage", "negative"],
      "used_for": ["lesion_text", "impression"]
    }
  ],
  "fallback_reason": null
}
```

当 RAG 不可用时：

```json
{
  "enabled": true,
  "status": "fallback",
  "retrieval_confidence": 0.0,
  "sources": [],
  "fallback_reason": "RAG knowledge base unavailable"
}
```

此时仍应返回规则模板生成的 `report_assist`，不能让整个 Orchestrator 任务失败。

### 9.3.1 llm_context

`llm_context` 用于记录报告辅助文本是否经过外部 LLM 增强，以及外部 LLM 调用是否成功。该字段只保存审计所需的元数据，不保存 API Key、不保存完整 prompt、不保存外部模型原始长文本响应。

推荐结构：

```json
{
  "enabled": true,
  "provider": "aliyun_bailian",
  "model": "qwen-plus",
  "status": "success",
  "prompt_version": "report_assist_v1",
  "fallback_reason": null
}
```

常见状态：

| status | 含义 |
| --- | --- |
| `disabled` | 外部 LLM 未开启，使用本地规则模板 |
| `success` | 阿里百炼调用成功，且输出通过结构化与安全检查 |
| `fallback` | 阿里百炼调用失败、超时或输出未通过检查，已回退到本地规则模板 |
| `blocked_by_privacy` | prompt 隐私检查未通过，禁止调用外部 LLM |

## 9.4 RAG/LLM 实现说明

RAG/LLM 的具体实现已经移动到：

```text
HeadCTOrchestrator/RAG报告辅助增强开发指导.md
```

阶段 I 只要求 Orchestrator 在结果结构中兼容以下字段：

- `report_assist.rag_enhanced`
- `report_assist.rag_context`
- `report_assist.llm_context`
- `report_assist.suggested_report_sections`
- `report_assist.recommended_actions`

RAG 专项文档中应继续维护：

- PostgreSQL + pgvector 或其他向量数据库方案。
- 知识库入库、embedding、向量检索和 fallback。
- 阿里百炼可选 LLM 接入策略。
- 脱敏、安全表达检查和审计要求。

## 10. can_enter_report 规则

建议：

```text
can_enter_report = true
```

仅表示可进入医生报告草稿工作流，不表示自动生成最终报告。

建议规则：

| 条件 | can_enter_report |
| --- | --- |
| Filter 成功，Lesion 成功，无重度质量限制 | true |
| Lesion 未配置 | false |
| Filter 失败 | false |
| Lesion 失败 | false |
| 重度伪影且配置跳过病灶识别 | false |
| 模型返回 strongly_limited_by_artifact | false 或附加强 warning |

## 11. 安全表述规则

禁止输出：

```text
确诊
排除
无需复核
无需医生审核
自动完成诊断
最终诊断为
```

推荐输出：

```text
疑似
未见明确
建议复核
可能受伪影影响
供医生参考
请结合临床与原始影像
```

## 12. RAG 模块衔接

RAG 知识库、向量数据库、pgvector、embedding、检索、阿里百炼 LLM 和安全检查不再放在本阶段文档中展开，统一维护在：

```text
HeadCTOrchestrator/RAG报告辅助增强开发指导.md
```

阶段 I 与 RAG 模块的衔接要求：

- 医生审核接口不直接依赖向量数据库可用性。
- RAG 失败时，Orchestrator 仍应返回基础 `report_assist`。
- 前端或上级平台可以展示 `rag_context.sources`，但不能把它当作最终诊断依据。
- 医生审核记录应保存医生是否采纳 AI/RAG 辅助文本。

## 13. 实现步骤

### Step 1：新增 review_store.py

职责：

- 校验 `task_id`。
- 读取任务目录。
- 写入 `review.json`。
- 追加 `review_events.jsonl`。
- 查询审核状态。

建议函数：

```python
def create_or_update_review(output_root: Path, task_id: str, payload: dict) -> dict:
    ...

def read_review(output_root: Path, task_id: str) -> dict:
    ...

def append_review_event(output_root: Path, task_id: str, event: dict) -> None:
    ...
```

### Step 2：兼容 report_assist 增强结果

阶段 I 不实现 RAG 细节，只要求审核闭环能读取和展示增强后的 `report_assist` 字段。

需要兼容：

```text
report_assist.rag_enhanced
report_assist.rag_context
report_assist.llm_context
report_assist.suggested_report_sections
report_assist.recommended_actions
```

注意：

- 如果 RAG 模块未启用，`report_assist` 仍应包含基础文本、warnings 和 `requires_doctor_review=true`。
- 如果 RAG 模块启用但失败，医生审核接口仍可正常提交和查询。
- 医生审核接口不能修改 `quality_control`、`lesion_analysis` 原始字段。

### Step 3：OrchestratorServer.py 增加审核接口

新增：

```python
@app.post(f"{API_PREFIX}/reviews/{{task_id}}")
async def create_review(task_id: str, payload: dict):
    ...

@app.get(f"{API_PREFIX}/reviews/{{task_id}}")
async def get_review(task_id: str):
    ...
```

### Step 4：更新 API_CONTRACT.md

新增：

```text
POST /api/head-ct-ai/reviews/{task_id}
GET  /api/head-ct-ai/reviews/{task_id}
```

补充：

- `report_assist.suggested_report_sections`
- `report_assist.recommended_actions`
- `report_assist.rag_context`、`report_assist.llm_context` 的可选透传字段
- 审核字段说明
- 审核状态枚举
- RAG/LLM 详细配置引用 `RAG报告辅助增强开发指导.md`
- 错误码

### Step 5：更新 SPRING_BOOT_CLIENT_EXAMPLE.md

补充：

- 提交医生审核。
- 查询医生审核。
- 报告模块读取 `report_assist` 与 `review`。
- 报告模块显示 `rag_context.sources`。
- 报告模块显示 `llm_context.provider`、`llm_context.model`、`llm_context.status`。

### Step 6：新增测试

建议文件：

```text
HeadCTOrchestrator/tests/test_orchestrator_reviews.py
```

测试项：

```text
test_get_review_pending_for_existing_task
test_create_review_for_success_task
test_create_review_requires_existing_task
test_review_status_validation
test_review_event_log_appended
test_review_does_not_modify_original_orchestrator_result
```

RAG/LLM 测试项移动到 `RAG报告辅助增强开发指导.md`。

## 14. 错误码建议

新增：

```text
INVALID_REVIEW_PAYLOAD
INVALID_REVIEW_STATUS
REVIEW_NOT_FOUND
TASK_NOT_SUCCESS
```

说明：

| 错误码 | 含义 |
| --- | --- |
| `INVALID_REVIEW_PAYLOAD` | 请求体不是合法审核结构 |
| `INVALID_REVIEW_STATUS` | 审核状态不在枚举范围内 |
| `REVIEW_NOT_FOUND` | 审核记录不存在，通常 GET 可返回 pending 代替 |
| `TASK_NOT_SUCCESS` | 不允许对未成功完成的任务提交确认类审核 |

## 15. 验收标准

阶段 I 完成时，应满足：

- 成功任务可提交医生审核。
- 未审核任务 GET 返回 `pending`。
- 审核后生成 `review.json`。
- 每次审核写入 `review_events.jsonl`。
- 原始 `orchestrator_result.json` 不被覆盖。
- `report_assist` 保留医生复核提示。
- 如果存在 `report_assist.rag_context` 和 `report_assist.llm_context`，医生审核接口应原样保留并可供上级平台展示。
- RAG/LLM 不可用时，医生审核接口仍可正常提交和查询。
- `suggested_report_sections.limitations` 必须包含 AI 辅助参考和医生复核提示。
- 禁止表述不会出现在 `report_assist` 中。
- 自动化测试通过。

## 16. 后续扩展

后续可以增加：

- 审核列表查询。
- 按医生、患者、日期检索审核记录。
- 接入数据库替代 JSON 文件。
- 报告草稿版本管理。
- 医生反馈反哺模型评估。
- 与上级平台报告模块做字段映射。
- 对 AI/RAG 辅助文本增加医生采纳率统计。
- 将医生修改记录沉淀为报告模板优化数据，但不直接反写模型诊断结果。
