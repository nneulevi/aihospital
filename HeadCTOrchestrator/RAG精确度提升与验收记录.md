# RAG 精确度提升与验收记录

更新时间：2026-06-23

## 本次完成内容

1. 长文本分块
   - 新增 `KnowledgeChunk` 数据结构。
   - 按 Markdown 标题优先切分，超长段落按最大字符数继续切分。
   - 默认参数：
     - `RAG_CHUNK_MAX_CHARS=900`
     - `RAG_CHUNK_OVERLAP_CHARS=160`
   - 每个 chunk 保留：
     - 原始文档 `source_document_id`
     - `chunk_id`
     - 标题、章节、标签、版本、语言等元数据。

2. 向量入库策略
   - `ingest_knowledge.py` 从“整文档入库”改为“chunk 入库”。
   - 重新入库前禁用旧整文档向量，避免新旧召回结果混杂。
   - 真实入库结果：

```json
{
  "status": "success",
  "document_count": 9,
  "chunk_count": 50
}
```

3. 召回结果增强
   - `retriever.py` 对外仍返回原始知识文档 `source_id`。
   - 同时新增 `chunk_id`，便于追踪具体命中的知识片段。
   - snippet 长度由 600 扩展为 800 字符。

4. 知识库扩展
   - 补充并扩展以下知识主题：
     - 金属伪影质控与报告表达
     - 颅内出血报告辅助规范
     - 报告模板
     - 安全表达规则
     - CQ500 标签说明
     - Orchestrator 合同说明
     - 临床分诊指导
     - 医生审核闭环
     - 模型结果解释规范

5. 兼容性修复
   - `parse_front_matter()` 支持 UTF-8 BOM。
   - 保持 RAG 对外返回结构兼容，新增字段采用扩展方式加入，遵守开闭原则。

6. AI 问诊/辅助诊断安全改写
   - `clinical_assist.py` 对外部 LLM 输出增加安全改写。
   - 当 LLM 返回“确诊”“无需复核”“无需医生审核”等禁用表达时，先改写为“AI 辅助提示”“需医生复核”“需医生审核”等可审核表达，再做二次校验。
   - 避免因外部 LLM 单次措辞不稳导致 Project2 真实业务链路 500。

## 验收结果

### RAG 组件单元测试

命令：

```powershell
python -m pytest HeadCTOrchestrator\tests\test_rag_components.py -q
```

结果：

```text
15 passed
```

### pgvector 入库校验

数据库检查结果：

```text
total=56
enabled=50
enabled_chunks=50
enabled_legacy_docs=0
enabled_source_docs=9
```

说明：当前启用的知识向量全部为 chunk，旧整文档向量已禁用。

### HNSW 召回 + DashScope rerank 校验

测试查询：

```text
头部外伤后头痛恶心，头颅CT存在金属伪影，报告如何表达并提醒医生复核
```

结果摘要：

```json
{
  "status": "success",
  "recall_count": 20,
  "top_rerank_provider": "dashscope",
  "top_source_id": "report_templates_v2",
  "top_chunk_id": "report_templates_v2#chunk-001"
}
```

### HeadCT AI/RAG 服务链 smoke 测试

命令：

```powershell
python scripts\smoke_test_headct_platform.py
```

结果摘要：

```json
{
  "orchestrator_status": "success",
  "filter_backend": "unet3d",
  "lesion_status": "success",
  "rag_status": "success",
  "llm_status": "success",
  "report_status": "released",
  "emr_status": "final"
}
```

复测结果：

```json
{
  "orchestrator_status": "success",
  "rag_status": "success",
  "llm_status": "success",
  "report_status": "released",
  "emr_status": "final"
}
```

### Project2 独立核心业务 E2E

命令：

```powershell
python scripts\e2e_project2_core_business.py
```

结果摘要：

```json
{
  "status": "success",
  "health": "UP",
  "orders_count": 3,
  "check_result_sections": {
    "checks": 1,
    "inspections": 1,
    "disposals": 1
  },
  "register_visit_state": "DIAGNOSIS_DONE",
  "prescription_status": "REFUNDED"
}
```

### Project2 + HeadCT AI 子系统真实业务 E2E

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
  "consultation_recommendation_count": 2,
  "diagnosis_suggestion_count": 1,
  "analysis_confidence": 0.4617331326007843,
  "report_service_status": "released",
  "emr_status": "final",
  "persisted": {
    "ai_consultation": 1,
    "ai_diagnosis_suggestion": 1,
    "ai_image_analysis": 1,
    "ai_generated_report": 1
  }
}
```

## 当前边界

- HeadCT AI/RAG 服务链端到端已通过。
- Project2 独立业务 E2E 已通过。
- Project2 + HeadCT AI 子系统真实业务 E2E 已通过。
- `-Reload` 模式下部分服务 stderr 日志出现大量 `PermissionError: [WinError 5] 拒绝访问。`，服务可用但日志会快速增大。建议后续将 reload 监听目录进一步收窄，或全链路验收时使用非 reload 模式。
