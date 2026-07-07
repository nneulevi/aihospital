# RAG 报告辅助增强开发指导

更新时间：2026-06-30

## 当前状态

本项目的 RAG 报告辅助增强已按标准链路接入：

1. 使用 DashScope Embedding 生成文本向量。
2. 使用 PostgreSQL + pgvector 存储知识向量。
3. 使用 HNSW 索引进行向量召回。
4. 使用 rerank 对候选知识片段重排。
5. 将模型结构化结果、医生上下文、RAG 证据片段一起提供给 LLM。
6. LLM 输出报告草稿后，进入医生审核、签名、发布与 EMR 归档流程。

## 标准 RAG 流程

```text
结构化 AI 结果
  -> 构造检索 query
  -> DashScope Embedding
  -> pgvector HNSW 召回
  -> rerank 重排
  -> 拼接可追溯证据
  -> LLM 生成报告草稿
  -> 安全规则检查
  -> 医生审核发布
```

## 接入要求

- 不允许把 RAG 结果直接作为最终诊断。
- 报告中应保留医生审核状态。
- RAG 证据需要保留 source、chunk_id、score，便于追溯。
- API Key、数据库密码不得提交到 Git。
- 开发环境通过 `HeadCTOrchestrator/scripts/headct_rag_env.local.ps1` 配置真实密钥。

## 验收要求

1. `rag/schema.sql` 已创建 pgvector 表、索引和必要字段。
2. `ingest_knowledge.py` 可以将 `rag/knowledge` 下的知识文档 embedding 入库。
3. `retriever.py` 返回向量召回和 rerank 后的证据。
4. `report_enhancer.py` 可以基于结构化 AI 结果生成报告辅助内容。
5. 端到端流程中报告草稿包含 RAG 增强证据，而不是纯模板文本。
6. 前端医生端显示 AI 置信度、报告内容、限制说明和医生审核状态。

## 后续补强

- 继续补充头部 CT 专业知识库，覆盖颅内出血分型、伪影影响、报告结构、随访建议。
- 对长上下文对话使用定期摘要和语义记忆召回。
- 将 RAG 召回证据与报告版本一并归档，保证报告生成过程可复查。
