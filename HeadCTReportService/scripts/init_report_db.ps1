$ErrorActionPreference = "Stop"

$ragEnv = Join-Path $PSScriptRoot "..\..\HeadCTOrchestrator\scripts\headct_rag_env.local.ps1"
if (-not $env:REPORT_DB_DSN -and (Test-Path $ragEnv)) {
    . $ragEnv
    $env:REPORT_DB_DSN = $env:RAG_DB_DSN
}

if (-not $env:REPORT_DB_DSN) {
    throw "REPORT_DB_DSN is not configured. Set it before initializing the report database."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Push-Location $repoRoot
try {
    python -c "from HeadCTReportService.db import Database; Database().initialize(); print('HeadCTReportService schema initialized')"
} finally {
    Pop-Location
}

