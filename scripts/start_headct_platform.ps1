param(
    [switch]$Restart,
    [switch]$Reload,
    [switch]$SkipProject2
)

$ErrorActionPreference = "Stop"

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$processPath = [Environment]::GetEnvironmentVariable("Path", "Process")
if (-not $processPath) {
    $processPath = [Environment]::GetEnvironmentVariable("PATH", "Process")
}
if ($processPath) {
    [Environment]::SetEnvironmentVariable("PATH", $null, "Process")
    [Environment]::SetEnvironmentVariable("Path", $processPath, "Process")
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$logDir = Join-Path $repoRoot ".tmp\headct-platform"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$ragEnv = Join-Path $repoRoot "HeadCTOrchestrator\scripts\headct_rag_env.local.ps1"
$ragEnvExample = Join-Path $repoRoot "HeadCTOrchestrator\scripts\headct_rag_env.example.ps1"
if (Test-Path $ragEnv) {
    . $ragEnv
} elseif (Test-Path $ragEnvExample) {
    Write-Host "RAG local env not found; using example/default environment. Copy HeadCTOrchestrator\scripts\headct_rag_env.example.ps1 to headct_rag_env.local.ps1 to enable real API keys."
    . $ragEnvExample
}

$project2Env = Join-Path $repoRoot "scripts\project2_env.local.ps1"
$project2EnvExample = Join-Path $repoRoot "scripts\project2_env.example.ps1"
if (Test-Path $project2Env) {
    . $project2Env
} elseif (Test-Path $project2EnvExample) {
    Write-Host "Project2 local env not found; using default database credentials. Copy scripts\project2_env.example.ps1 to project2_env.local.ps1 when local PostgreSQL does not use postgres/postgres."
}

if (-not $env:RAG_DB_DSN) {
    $env:RAG_DB_DSN = "postgresql://postgres:postgres@localhost:5432/headct_rag"
}
if (-not $env:PROJECT2_DB_USERNAME) {
    $env:PROJECT2_DB_USERNAME = "postgres"
}
if (-not $env:PROJECT2_DB_PASSWORD) {
    $env:PROJECT2_DB_PASSWORD = "postgres"
}
if (-not $env:PROJECT2_DB_URL) {
    $env:PROJECT2_DB_URL = "jdbc:postgresql://localhost:5432/hospital?useSSL=false&serverTimezone=Asia/Shanghai&characterEncoding=utf8"
}
if (-not $env:HEADCT_LOCAL_EMR_TOKEN) {
    $env:HEADCT_LOCAL_EMR_TOKEN = "headct-local-emr-change-before-production"
}

$env:REPORT_DB_DSN = $env:RAG_DB_DSN
$env:EMR_DB_DSN = $env:RAG_DB_DSN
$env:EMR_SERVICE_TOKEN = $env:HEADCT_LOCAL_EMR_TOKEN
$env:EMR_ENABLED = "true"
$env:EMR_BASE_URL = "http://127.0.0.1:8040"
$env:ORCHESTRATOR_BASE_URL = "http://127.0.0.1:8010"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:WATCHFILES_IGNORE_PERMISSION_DENIED = "1"

$filterMatureCheckpoint = Join-Path $repoRoot "Filter\model\external_weights\metal_artifact_segmentation\mature_metal_artifact_unet3d.pt"
$filterMatureMarCheckpoint = Join-Path $repoRoot "Filter\model\external_weights\metal_artifact_reduction\InDuDoNet_latest.pt"
$filterLocalCheckpoint = Join-Path $repoRoot "Filter\model\runs\metal_unet3d\best_unet3d_metal.pt"
$filterSmokeCheckpoint = Join-Path $repoRoot "Filter\model\runs\config_visual_smoke\best_unet3d_metal.pt"
$env:CT_MATURE_MAR_CHECKPOINT_PATH = $filterMatureMarCheckpoint
$env:CT_MATURE_MAR_MODEL_NAME = "InDuDoNet"
$env:CT_MATURE_MAR_TASK_TYPE = "metal_artifact_reduction"
$env:CT_MATURE_CANDIDATE_PATH = $filterMatureCheckpoint
if (Test-Path $filterMatureCheckpoint) {
    $env:CT_MODEL_WEIGHT_PATH = $filterMatureCheckpoint
    $env:CT_CHECKPOINT_PROVENANCE = "mature_public_external"
    $env:CT_CHECKPOINT_FALLBACK_USED = "false"
    $env:CT_MODEL_NAME = "mature_public_metal_artifact_segmentation"
    $env:CT_MODEL_VERSION = "external-mature"
} elseif (Test-Path $filterLocalCheckpoint) {
    $env:CT_MODEL_WEIGHT_PATH = $filterLocalCheckpoint
    $env:CT_CHECKPOINT_PROVENANCE = "local_project_trained"
    $env:CT_CHECKPOINT_FALLBACK_USED = "false"
    $env:CT_MATURE_CANDIDATE_PATH = $filterMatureCheckpoint
    $env:CT_MODEL_NAME = "metal_unet3d_local"
    $env:CT_MODEL_VERSION = "local-trained"
} else {
    $env:CT_MODEL_WEIGHT_PATH = $filterSmokeCheckpoint
    $env:CT_CHECKPOINT_PROVENANCE = "smoke_fallback"
    $env:CT_CHECKPOINT_FALLBACK_USED = "true"
    $env:CT_MATURE_CANDIDATE_PATH = $filterMatureCheckpoint
    $env:CT_MODEL_NAME = "metal_unet3d_smoke"
    $env:CT_MODEL_VERSION = "smoke-link-test"
}
Remove-Item Env:CT_SERVER_DEVICE -ErrorAction SilentlyContinue

$env:LESION_MODE = "model"
$env:LESION_PORT = "8021"
$hemorrhageSmokeCheckpoint = Join-Path $repoRoot "HeadCTLesionDetection\models\hemorrhage\runs\hemorrhage_v1\smoke_best.pt"
$hemorrhageLocalCheckpoint = Join-Path $repoRoot "HeadCTLesionDetection\models\hemorrhage\runs\hemorrhage_v1\best.pt"
$vinbigdataExternalDir = Join-Path $repoRoot "HeadCTLesionDetection\models\hemorrhage\external_weights"
$vinbigdataScriptedCheckpoint = Join-Path $vinbigdataExternalDir "vinbigdata_midl2020_cnn_lstm.pt"
$vinbigdataTorchscriptCheckpoint = Join-Path $vinbigdataExternalDir "vinbigdata_midl2020_cnn_lstm.torchscript.pt"
$vinbigdataRawResnetCheckpoint = Join-Path $vinbigdataExternalDir "best_resnet50.pth"
$vinbigdataCalibrationPath = Join-Path $repoRoot "HeadCTLesionDetection\models\hemorrhage\runs\vinbigdata_cq500_calibration\calibration.json"
$ichsegExternalDir = Join-Path $vinbigdataExternalDir "ichseg_rank_nnunet"
$env:ICHSEG_CHECKPOINT = Join-Path $ichsegExternalDir "fold_0\checkpoint_final.pth"
$env:ICHSEG_PLANS = Join-Path $ichsegExternalDir "nnUNetPlans.json"
$env:ICHSEG_MANIFEST = Join-Path $ichsegExternalDir "manifest.json"
if ((Test-Path $env:ICHSEG_CHECKPOINT) -and (Test-Path $env:ICHSEG_PLANS)) {
    $env:ICHSEG_ENABLED = "true"
    $env:ICHSEG_RUNTIME_STATUS = "enabled_executable"
    if (-not $env:ICHSEG_INFERENCE_SHAPE) {
        $env:ICHSEG_INFERENCE_SHAPE = "16,192,192"
    }
} else {
    $env:ICHSEG_ENABLED = "false"
    $env:ICHSEG_RUNTIME_STATUS = "checkpoint_registered_not_yet_executed_by_lesion_service"
}
if (Test-Path $vinbigdataScriptedCheckpoint) {
    $env:HEMORRHAGE_MODEL_PROVIDER = "vinbigdata"
    $env:VINBIGDATA_CHECKPOINT = $vinbigdataScriptedCheckpoint
    $env:HEMORRHAGE_CHECKPOINT = $hemorrhageSmokeCheckpoint
    $env:HEMORRHAGE_CHECKPOINT_PROVENANCE = "mature_public_external"
    $env:HEMORRHAGE_CHECKPOINT_FALLBACK_USED = "false"
} elseif (Test-Path $vinbigdataTorchscriptCheckpoint) {
    $env:HEMORRHAGE_MODEL_PROVIDER = "vinbigdata"
    $env:VINBIGDATA_CHECKPOINT = $vinbigdataTorchscriptCheckpoint
    $env:HEMORRHAGE_CHECKPOINT = $hemorrhageSmokeCheckpoint
    $env:HEMORRHAGE_CHECKPOINT_PROVENANCE = "mature_public_external"
    $env:HEMORRHAGE_CHECKPOINT_FALLBACK_USED = "false"
} elseif (Test-Path $vinbigdataRawResnetCheckpoint) {
    $env:HEMORRHAGE_MODEL_PROVIDER = "vinbigdata"
    $env:VINBIGDATA_CHECKPOINT = $vinbigdataRawResnetCheckpoint
    $env:HEMORRHAGE_CHECKPOINT = $hemorrhageSmokeCheckpoint
    $env:HEMORRHAGE_CHECKPOINT_PROVENANCE = "mature_public_external_raw"
    $env:HEMORRHAGE_CHECKPOINT_FALLBACK_USED = "false"
} elseif (Test-Path $hemorrhageLocalCheckpoint) {
    $env:HEMORRHAGE_MODEL_PROVIDER = "local"
    $env:VINBIGDATA_CHECKPOINT = $vinbigdataScriptedCheckpoint
    $env:HEMORRHAGE_CHECKPOINT = $hemorrhageLocalCheckpoint
    $env:HEMORRHAGE_CHECKPOINT_PROVENANCE = "local_project_trained"
    $env:HEMORRHAGE_CHECKPOINT_FALLBACK_USED = "true"
} else {
    $env:HEMORRHAGE_MODEL_PROVIDER = "local"
    $env:VINBIGDATA_CHECKPOINT = $vinbigdataScriptedCheckpoint
    $env:HEMORRHAGE_CHECKPOINT = $hemorrhageSmokeCheckpoint
    $env:HEMORRHAGE_CHECKPOINT_PROVENANCE = "smoke_fallback"
    $env:HEMORRHAGE_CHECKPOINT_FALLBACK_USED = "true"
}
$env:HEMORRHAGE_FALLBACK_CHECKPOINT = $hemorrhageSmokeCheckpoint
$env:HEMORRHAGE_MATURE_CANDIDATE_PATHS = "$vinbigdataScriptedCheckpoint;$vinbigdataTorchscriptCheckpoint;$vinbigdataRawResnetCheckpoint"
$env:HEMORRHAGE_ALLOW_INFERENCE_FALLBACK = "false"
$env:HEMORRHAGE_DEVICE = "auto"
if (-not $env:VINBIGDATA_SAMPLING_OFFSETS) {
    $env:VINBIGDATA_SAMPLING_OFFSETS = "-0.25,0,0.25"
}
if (-not $env:VINBIGDATA_TTA_FLIP) {
    $env:VINBIGDATA_TTA_FLIP = "true"
}
if (Test-Path $vinbigdataCalibrationPath) {
    try {
        $calibration = Get-Content -Raw -Encoding UTF8 $vinbigdataCalibrationPath | ConvertFrom-Json
        $isUnsupervised = [string]$calibration.source -eq "cq500ct200_unsupervised_distribution"
        $allowUnsupervised = $env:VINBIGDATA_ALLOW_UNSUPERVISED_CALIBRATION -eq "true"
        if (-not $isUnsupervised -or $allowUnsupervised) {
            $env:VINBIGDATA_CALIBRATION_PATH = $vinbigdataCalibrationPath
            if ($calibration.recommended_threshold -ne $null) {
                $env:VINBIGDATA_THRESHOLD = [string]$calibration.recommended_threshold
            }
        } else {
            Write-Host "VinBigData calibration is unsupervised distribution-only; not applying as runtime threshold. Set VINBIGDATA_ALLOW_UNSUPERVISED_CALIBRATION=true to opt in."
        }
    } catch {
        Write-Host "VinBigData calibration exists but cannot be parsed; using configured/default threshold."
    }
}

$env:FILTER_BASE_URL = "http://127.0.0.1:8000"
$env:LESION_SERVICE_ENABLED = "true"
$env:LESION_BASE_URL = "http://127.0.0.1:8021"
$env:LESION_REQUESTED_TYPES = "hemorrhage"

function Test-ServiceHealth([string]$Url) {
    try {
        Invoke-RestMethod -Uri $Url -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Stop-PortListeners([int]$Port) {
    $lines = netstat -ano | Select-String ":$Port"
    $listenerPids = @()
    foreach ($line in $lines) {
        if ($line.Line -match "LISTENING\s+(\d+)$") {
            $listenerPids += [int]$Matches[1]
        }
    }
    $listenerPids = $listenerPids | Sort-Object -Unique
    foreach ($processId in $listenerPids) {
        Write-Host "Stopping listener on port ${Port}: PID $processId"
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

function Start-PythonService(
    [string]$Name,
    [string]$Module,
    [int]$Port,
    [string]$HealthUrl,
    [string[]]$ReloadDirs,
    [bool]$AllowReload = $true
) {
    if ($Restart) {
        Stop-PortListeners $Port
        Start-Sleep -Milliseconds 800
    } elseif (Test-ServiceHealth $HealthUrl) {
        Write-Host "$Name already running: $HealthUrl"
        return
    } else {
        Stop-PortListeners $Port
    }

    $arguments = @("-m", "uvicorn", $Module, "--host", "127.0.0.1", "--port", [string]$Port)
    $allowUvicornReload = $env:HEADCT_ALLOW_UVICORN_RELOAD -eq "true"
    $useReload = $Reload -and $AllowReload -and $allowUvicornReload
    if ($Reload -and $AllowReload -and -not $allowUvicornReload) {
        Write-Host "$Name safe reload requested; uvicorn --reload disabled to avoid Windows stderr PermissionError growth. Set HEADCT_ALLOW_UVICORN_RELOAD=true to force it."
    }
    if ($useReload) {
        $arguments += "--reload"
        foreach ($dir in $ReloadDirs) {
            $reloadPath = Join-Path $repoRoot $dir
            if (Test-Path $reloadPath) {
                $arguments += @("--reload-dir", (Resolve-Path $reloadPath).Path)
            }
        }
        $arguments += @(
            "--reload-include", "*.py",
            "--reload-exclude", ".git",
            "--reload-exclude", ".tmp",
            "--reload-exclude", ".m2",
            "--reload-exclude", ".maven",
            "--reload-exclude", "__pycache__",
            "--reload-exclude", "*.log",
            "--reload-exclude", "orchestrator_outputs",
            "--reload-exclude", "lesion_outputs",
            "--reload-exclude", "filter_outputs"
        )
    }

    $stdout = Join-Path $logDir "$Name.stdout.log"
    $stderr = Join-Path $logDir "$Name.stderr.log"
    Remove-Item $stdout, $stderr -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory $repoRoot `
        -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr | Out-Null
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        Start-Sleep -Milliseconds 500
        if (Test-ServiceHealth $HealthUrl) {
            $mode = if ($useReload) { "reload" } else { "normal" }
            Write-Host "$Name started ($mode): $HealthUrl"
            return
        }
    }
    throw "$Name failed to start. See $stderr"
}

function Start-Project2Service() {
    $healthUrl = "http://127.0.0.1:8092/actuator/health"
    if ($Restart) {
        Stop-PortListeners 8092
        Start-Sleep -Milliseconds 800
    } elseif (Test-ServiceHealth $healthUrl) {
        Write-Host "project2 already running: $healthUrl"
        return
    } else {
        Stop-PortListeners 8092
    }

    $workdir = Join-Path $repoRoot "Project2"
    $stdout = Join-Path $logDir "project2.stdout.log"
    $stderr = Join-Path $logDir "project2.stderr.log"
    Remove-Item $stdout, $stderr -Force -ErrorAction SilentlyContinue
    $env:MAVEN_USER_HOME = Join-Path $repoRoot ".maven"
    $mavenRepo = Join-Path $repoRoot ".m2\repository"
    $arguments = @(
        "-q",
        "spring-boot:run",
        "-DskipTests",
        "-Dmaven.test.skip=true",
        "-Dmaven.repo.local=$mavenRepo"
    )
    Start-Process -FilePath (Join-Path $workdir "mvnw.cmd") -ArgumentList $arguments -WorkingDirectory $workdir `
        -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr | Out-Null
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        Start-Sleep -Seconds 1
        if (Test-ServiceHealth $healthUrl) {
            Write-Host "project2 started: $healthUrl"
            return
        }
    }
    throw "project2 failed to start. See $stderr"
}

Start-PythonService "filter" "Filter.Fastapi.CTDetectionServer:app" 8000 "http://127.0.0.1:8000/api/ct-artifact/health" @("Filter\Fastapi", "Filter\model") $false
Start-PythonService "lesion" "HeadCTLesionDetection.LesionDetectionServer:app" 8021 "http://127.0.0.1:8021/api/head-ct-lesion/health" @("HeadCTLesionDetection") $false
Start-PythonService "orchestrator" "HeadCTOrchestrator.OrchestratorServer:app" 8010 "http://127.0.0.1:8010/api/head-ct-ai/health" @("HeadCTOrchestrator") $true
Start-PythonService "emr" "HeadCTEMRService.EmrServer:app" 8040 "http://127.0.0.1:8040/api/v1/health" @("HeadCTEMRService") $true
Start-PythonService "report" "HeadCTReportService.ReportServer:app" 8030 "http://127.0.0.1:8030/api/v1/health" @("HeadCTReportService") $true

if (-not $SkipProject2) {
    Start-Project2Service
}

Write-Host "Head CT platform services are ready."
Write-Host "Report workspace: http://127.0.0.1:8030"
Write-Host "Project2 API: http://127.0.0.1:8092"
