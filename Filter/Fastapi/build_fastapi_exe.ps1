param(
  [string]$Name = "CTDetectionServer",
  [string]$Entry = "CTDetectionServer.py"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
  pyinstaller `
    --noconfirm `
    --clean `
    --name $Name `
    --add-data "..\model;model" `
    --add-data "frontend;frontend" `
    $Entry
} finally {
  Pop-Location
}
