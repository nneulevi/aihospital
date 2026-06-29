param(
    [Parameter(Mandatory=$true)]
    [string]$PostgresPassword,

    [string]$Database = "headct_rag",
    [string]$AppUser = "headct_rag",
    [string]$AppPassword = "HeadCT_RAG_Local_ChangeMe_2026",
    [string]$ProjectRoot = "D:\exam"
)

$ErrorActionPreference = "Stop"

$PgRoot = "D:\PostgreSQL"
$PgBin = Join-Path $PgRoot "bin"
$Psql = Join-Path $PgBin "psql.exe"
$VectorControl = Join-Path $PgRoot "share\extension\vector.control"
$SchemaPath = Join-Path $ProjectRoot "HeadCTOrchestrator\rag\schema.sql"

if (-not (Test-Path $Psql)) {
    throw "psql.exe not found at $Psql"
}
if (-not (Test-Path $SchemaPath)) {
    throw "schema.sql not found at $SchemaPath"
}
if (-not (Test-Path $VectorControl)) {
    throw "pgvector server extension is missing: $VectorControl. Install pgvector for PostgreSQL 17 before initializing schema."
}

$env:Path = "$PgBin;$env:Path"
$env:PGPASSWORD = $PostgresPassword

$roleSql = @"
DO `$do`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$AppUser') THEN
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', '$AppUser', '$AppPassword');
    ELSE
        EXECUTE format('ALTER ROLE %I WITH LOGIN PASSWORD %L', '$AppUser', '$AppPassword');
    END IF;
END
`$do`$;
"@

& $Psql -h localhost -p 5432 -U postgres -d postgres -v ON_ERROR_STOP=1 -c $roleSql

$dbExists = (@(& $Psql -h localhost -p 5432 -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$Database'") -join "").Trim()
if ($dbExists -ne "1") {
    & $Psql -h localhost -p 5432 -U postgres -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $Database OWNER $AppUser ENCODING 'UTF8'"
}

& $Psql -h localhost -p 5432 -U postgres -d $Database -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS vector"

$env:PGPASSWORD = $AppPassword
& $Psql -h localhost -p 5432 -U $AppUser -d $Database -v ON_ERROR_STOP=1 -f $SchemaPath

$localEnv = Join-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) "headct_rag_env.local.ps1"
@"
`$env:Path = "D:\PostgreSQL\bin;`$env:Path"
`$env:RAG_ENABLED = "true"
`$env:RAG_VECTOR_BACKEND = "pgvector"
`$env:RAG_DB_DSN = "postgresql://${AppUser}:${AppPassword}@localhost:5432/$Database"
`$env:RAG_STRICT_MODE = "true"
`$env:RAG_TOP_K = "5"
`$env:RAG_RECALL_TOP_N = "20"
`$env:RAG_MIN_SIMILARITY = "0.05"
`$env:RAG_EMBEDDING_DIM = "1536"
`$env:RAG_EMBEDDING_PROVIDER = "dashscope"
`$env:RAG_HNSW_EF_SEARCH = "80"
`$env:RAG_RERANK_ENABLED = "true"
`$env:RAG_RERANK_PROVIDER = "dashscope"
`$env:RAG_RERANK_TOP_N = "5"
`$env:RAG_RERANK_TIMEOUT_SECONDS = "30"
`$env:DASHSCOPE_API_KEY = `$env:ALI_BAILIAN_API_KEY
`$env:DASHSCOPE_EMBEDDING_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
`$env:DASHSCOPE_EMBEDDING_MODEL = "text-embedding-v4"
`$env:DASHSCOPE_EMBEDDING_TIMEOUT_SECONDS = "30"
`$env:DASHSCOPE_RERANK_BASE_URL = "https://dashscope.aliyuncs.com"
`$env:DASHSCOPE_RERANK_MODEL = "gte-rerank-v2"
`$env:LLM_ENABLED = "false"
`$env:LLM_PROVIDER = "aliyun_bailian"
`$env:LLM_STRICT_MODE = "true"
`$env:ALI_BAILIAN_API_KEY = ""
`$env:ALI_BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
`$env:ALI_BAILIAN_MODEL = "qwen-plus"
`$env:ALI_BAILIAN_TIMEOUT_SECONDS = "30"
"@ | Set-Content -Path $localEnv -Encoding UTF8

Write-Host "Database initialized: $Database"
Write-Host "Local env file written: $localEnv"
Write-Host "Next: replace ALI_BAILIAN_API_KEY in $localEnv, dot-source it, then run knowledge ingestion."
