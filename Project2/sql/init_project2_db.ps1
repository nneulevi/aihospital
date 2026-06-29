param(
    [string]$HostName = "localhost",
    [int]$Port = 5432,
    [string]$Database = "hospital",
    [string]$User = "postgres",
    [string]$PsqlPath = "psql"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$schemaPath = Join-Path $scriptDir "001_project2_schema.sql"
if (-not (Test-Path $schemaPath)) {
    throw "Missing schema file: $schemaPath"
}

& $PsqlPath -h $HostName -p $Port -U $User -d $Database -v ON_ERROR_STOP=1 -f $schemaPath
if ($LASTEXITCODE -ne 0) {
    throw "Project2 database schema initialization failed."
}

Write-Host "Project2 database schema is ready: $Database"
