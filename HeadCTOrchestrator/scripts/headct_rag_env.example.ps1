# HeadCT RAG local environment for PowerShell.
# Copy this file to headct_rag_env.local.ps1, replace secrets, then run:
#   . .\HeadCTOrchestrator\scripts\headct_rag_env.local.ps1

$env:Path = "D:\PostgreSQL\bin;$env:Path"

$env:RAG_ENABLED = "true"
$env:RAG_VECTOR_BACKEND = "pgvector"
$env:RAG_DB_DSN = "postgresql://headct_rag:REPLACE_WITH_DB_PASSWORD@localhost:5432/headct_rag"
$env:RAG_STRICT_MODE = "true"
$env:RAG_TOP_K = "5"
$env:RAG_RECALL_TOP_N = "20"
$env:RAG_MIN_SIMILARITY = "0.05"
$env:RAG_EMBEDDING_DIM = "1536"
$env:RAG_EMBEDDING_PROVIDER = "dashscope"
$env:RAG_HNSW_EF_SEARCH = "80"
$env:RAG_RERANK_ENABLED = "true"
$env:RAG_RERANK_PROVIDER = "dashscope"
$env:RAG_RERANK_TOP_N = "5"
$env:RAG_RERANK_TIMEOUT_SECONDS = "30"
$env:DASHSCOPE_API_KEY = ""
$env:DASHSCOPE_EMBEDDING_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:DASHSCOPE_EMBEDDING_MODEL = "text-embedding-v4"
$env:DASHSCOPE_EMBEDDING_TIMEOUT_SECONDS = "30"
$env:DASHSCOPE_RERANK_BASE_URL = "https://dashscope.aliyuncs.com"
$env:DASHSCOPE_RERANK_MODEL = "gte-rerank-v2"

$env:LLM_ENABLED = "false"
$env:LLM_PROVIDER = "aliyun_bailian"
$env:LLM_STRICT_MODE = "true"
$env:ALI_BAILIAN_API_KEY = ""
$env:ALI_BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:ALI_BAILIAN_MODEL = "qwen-plus"
$env:ALI_BAILIAN_TIMEOUT_SECONDS = "30"
