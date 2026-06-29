# RAG 报告辅助增强接入记录

更新时间：2026-06-12

## 1. 当前结论

标准 RAG 链路已完成真实验证：

```text
DashScope text-embedding-v4
-> PostgreSQL + pgvector HNSW 召回
-> DashScope gte-rerank-v2 二阶段重排
-> top_k 证据片段
-> 阿里百炼 qwen-plus 报告辅助生成
-> safety_rules 医疗安全校验
```

本次已完成：

- 使用 DashScope embedding 对知识库重新入库。
- 使用 pgvector HNSW 召回。
- 使用 DashScope rerank 真实重排。
- 自动化测试通过。

## 2. 已完成代码改造

新增/更新：

```text
HeadCTOrchestrator/rag/embedding_provider.py
HeadCTOrchestrator/rag/reranker.py
HeadCTOrchestrator/rag/retriever.py
HeadCTOrchestrator/rag/schema.sql
HeadCTOrchestrator/config.py
HeadCTOrchestrator/rag/config.py
HeadCTOrchestrator/scripts/headct_rag_check.ps1
HeadCTOrchestrator/scripts/headct_rag_env.example.ps1
HeadCTOrchestrator/scripts/headct_rag_init_db.ps1
```

关键能力：

- `RAG_EMBEDDING_PROVIDER=dashscope` 时调用 DashScope `/embeddings`。
- 默认 embedding 模型：`text-embedding-v4`。
- 默认向量维度：`1536`。
- pgvector 索引从 `ivfflat` 迁移为 `hnsw`。
- `retriever.py` 支持 `RAG_RECALL_TOP_N` 粗召回。
- `retriever.py` 已设置 `hnsw.ef_search`。
- `reranker.py` 支持 DashScope `gte-rerank-v2` 二阶段重排。
- 常规 pytest 显式隔离外部 API，避免测试消耗 API 或受网络波动影响。

## 3. 数据库状态

PostgreSQL：

```text
D:\PostgreSQL
PostgreSQL 17.10
pgvector 0.8.2
database: headct_rag
table: rag_documents
document_count: 6
embedding_dim: 1536
```

HNSW 索引已确认存在：

```sql
CREATE INDEX idx_rag_documents_embedding_hnsw
ON public.rag_documents
USING hnsw (embedding vector_cosine_ops)
WITH (m='16', ef_construction='64');
```

## 4. 当前配置

本地环境文件：

```text
HeadCTOrchestrator/scripts/headct_rag_env.local.ps1
```

关键配置：

```powershell
$env:RAG_EMBEDDING_PROVIDER = "dashscope"
$env:DASHSCOPE_EMBEDDING_MODEL = "text-embedding-v4"
$env:RAG_RECALL_TOP_N = "20"
$env:RAG_HNSW_EF_SEARCH = "80"
$env:RAG_RERANK_ENABLED = "true"
$env:RAG_RERANK_PROVIDER = "dashscope"
$env:DASHSCOPE_RERANK_MODEL = "gte-rerank-v2"
```

检查命令：

```powershell
. HeadCTOrchestrator\scripts\headct_rag_env.local.ps1
powershell -ExecutionPolicy Bypass -File HeadCTOrchestrator\scripts\headct_rag_check.ps1
```

检查脚本已脱敏输出 `RAG_DB_DSN`、`ALI_BAILIAN_API_KEY`、`DASHSCOPE_API_KEY`。

## 5. DashScope Embedding 入库验证

执行命令：

```powershell
. HeadCTOrchestrator\scripts\headct_rag_env.local.ps1
python -m HeadCTOrchestrator.rag.ingest_knowledge
```

结果：

```json
{
  "status": "success",
  "document_count": 6
}
```

说明：

```text
知识库 6 个 Markdown 文档已使用 DashScope text-embedding-v4 重新生成向量，并写入 rag_documents.embedding。
```

## 6. HNSW + Rerank 验证

测试查询：

```text
head ct moderate metal artifact intracranial hemorrhage negative report doctor review
```

验证结果摘要：

```json
{
  "status": "success",
  "recall_count": 6,
  "source_count": 5,
  "sources": [
    {
      "source_id": "cq500_label_notes_v1",
      "rerank_provider": "dashscope",
      "rerank_score": 0.19394592898867585
    },
    {
      "source_id": "artifact_quality_v1",
      "rerank_provider": "dashscope",
      "rerank_score": 0.1843810808727244
    },
    {
      "source_id": "orchestrator_contract_v1",
      "rerank_provider": "dashscope",
      "rerank_score": 0.18220571518044376
    },
    {
      "source_id": "safety_expression_rules_v1",
      "rerank_provider": "dashscope",
      "rerank_score": 0.17434656754821085
    },
    {
      "source_id": "hemorrhage_reporting_v1",
      "rerank_provider": "dashscope",
      "rerank_score": 0.1619427938875571
    }
  ]
}
```

验收点：

- `recall_count = 6`
- `source_count = 5`
- `sources[*].rerank_provider = "dashscope"`
- `sources[*].rerank_score` 存在
- 检索结果可进入 `report_assist.rag_context.sources`

## 7. 已完成测试

常规自动化测试：

```powershell
python -m pytest HeadCTOrchestrator/tests -q
```

结果：

```text
28 passed
```

## 8. 验收状态

已完成：

- PostgreSQL + pgvector。
- HNSW 索引。
- DashScope embedding provider。
- DashScope embedding 重新入库。
- DashScope rerank provider。
- HNSW recall + DashScope rerank 检索流程。
- 阿里百炼 LLM 报告增强。
- safety_rules 校验。

当前 RAG 模块已从“链路通原型”升级为标准 RAG 验证通过版本。
