$services = @(
    @{ Name = "Filter"; Url = "http://127.0.0.1:8000/api/ct-artifact/health" },
    @{ Name = "Orchestrator"; Url = "http://127.0.0.1:8010/api/head-ct-ai/health" },
    @{ Name = "LesionDetection"; Url = "http://127.0.0.1:8021/api/head-ct-lesion/health" },
    @{ Name = "ReportService"; Url = "http://127.0.0.1:8030/api/v1/health" },
    @{ Name = "EMRService"; Url = "http://127.0.0.1:8040/api/v1/health" }
)

$results = foreach ($service in $services) {
    try {
        $payload = Invoke-RestMethod -Uri $service.Url -TimeoutSec 5
        [PSCustomObject]@{ Service = $service.Name; Status = $payload.status; Url = $service.Url }
    } catch {
        [PSCustomObject]@{ Service = $service.Name; Status = "unavailable"; Url = $service.Url }
    }
}

$results | Format-Table -AutoSize
if ($results.Status -contains "unavailable" -or $results.Status -contains "degraded") {
    exit 1
}

