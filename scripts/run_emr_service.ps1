$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
. (Join-Path $repoRoot "HeadCTOrchestrator\scripts\headct_rag_env.local.ps1")
$env:EMR_DB_DSN = $env:RAG_DB_DSN
$env:EMR_SERVICE_TOKEN = if ($env:HEADCT_LOCAL_EMR_TOKEN) { $env:HEADCT_LOCAL_EMR_TOKEN } else { "headct-local-emr-change-before-production" }
$env:PYTHONDONTWRITEBYTECODE = "1"
Set-Location $repoRoot
python -m uvicorn HeadCTEMRService.EmrServer:app --host 127.0.0.1 --port 8040

