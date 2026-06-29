$ErrorActionPreference = "Stop"

$PgRoot = "D:\PostgreSQL"
$PgBin = Join-Path $PgRoot "bin"
$Psql = Join-Path $PgBin "psql.exe"
$PgHba = Join-Path $PgRoot "data\pg_hba.conf"
$VectorControl = Join-Path $PgRoot "share\extension\vector.control"

Write-Host "== HeadCT RAG PostgreSQL check =="
Write-Host "PGROOT: $PgRoot"

if (-not (Test-Path $Psql)) {
    throw "psql.exe not found at $Psql"
}

& $Psql --version

$service = Get-Service postgresql-x64-17 -ErrorAction SilentlyContinue
if ($null -eq $service) {
    Write-Warning "PostgreSQL service postgresql-x64-17 was not found."
} else {
    Write-Host "Service: $($service.Name) $($service.Status) $($service.StartType)"
}

if (Test-Path $PgHba) {
    Write-Host "pg_hba.conf: $PgHba"
} else {
    Write-Warning "pg_hba.conf not found at $PgHba"
}

if (Test-Path $VectorControl) {
    Write-Host "pgvector server extension: installed ($VectorControl)"
} else {
    Write-Warning "pgvector server extension is NOT installed. CREATE EXTENSION vector will fail until vector.control exists."
}

$pathHasPg = ($env:Path -split ";") -contains $PgBin
if ($pathHasPg) {
    Write-Host "PATH: contains $PgBin"
} else {
    Write-Warning "PATH does not contain $PgBin. Use: `$env:Path = '$PgBin;' + `$env:Path"
}

foreach ($name in @("RAG_DB_DSN", "ALI_BAILIAN_API_KEY", "DASHSCOPE_API_KEY")) {
    $value = [Environment]::GetEnvironmentVariable($name, "Process")
    if ([string]::IsNullOrWhiteSpace($value) -or $value -like "REPLACE_WITH_*") {
        Write-Warning "$name is not set in current process."
    } elseif ($name -in @("ALI_BAILIAN_API_KEY", "DASHSCOPE_API_KEY")) {
        Write-Host "${name}: set"
    } elseif ($name -eq "RAG_DB_DSN") {
        $masked = $value -replace "://([^:/@]+):([^@]+)@", '://$1:***@'
        Write-Host "${name}: $masked"
    } else {
        Write-Host "${name}: $value"
    }
}

foreach ($name in @("RAG_EMBEDDING_PROVIDER", "DASHSCOPE_EMBEDDING_MODEL", "RAG_RERANK_ENABLED", "RAG_RERANK_PROVIDER", "DASHSCOPE_RERANK_MODEL")) {
    $value = [Environment]::GetEnvironmentVariable($name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Warning "$name is not set in current process."
    } else {
        Write-Host "${name}: $value"
    }
}
