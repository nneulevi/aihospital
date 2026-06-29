$ErrorActionPreference = "Stop"

$ragEnv = Join-Path $PSScriptRoot "..\..\HeadCTOrchestrator\scripts\headct_rag_env.local.ps1"
if (-not $env:REPORT_DB_DSN -and (Test-Path $ragEnv)) {
    . $ragEnv
    $env:REPORT_DB_DSN = $env:RAG_DB_DSN
}

if (-not $env:REPORT_DB_DSN) {
    throw "REPORT_DB_DSN is not configured."
}

if (-not $env:ORCHESTRATOR_BASE_URL) {
    $env:ORCHESTRATOR_BASE_URL = "http://localhost:8010"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Push-Location $repoRoot
try {
    python -m uvicorn HeadCTReportService.ReportServer:app --host 0.0.0.0 --port 8030
} finally {
    Pop-Location
}

