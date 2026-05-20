param(
    [int]$Port = 8006,
    [string]$BackendUrl = "",
    [switch]$Detached
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Note: the ChatGPT/MCP app surface is optional/quarantined, not the primary local workflow." -ForegroundColor Yellow

function Test-PortAvailable {
    param([int]$CandidatePort)

    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $CandidatePort)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Resolve-BackendUrl {
    param([string]$PreferredUrl)

    if ($PreferredUrl) {
        return $PreferredUrl
    }

    $candidatePorts = 8005, 8000, 8001, 8002, 8003, 8004, 8007, 8008, 8009, 8010
    foreach ($candidatePort in $candidatePorts) {
        try {
            $response = Invoke-RestMethod "http://127.0.0.1:$candidatePort/openapi.json" -TimeoutSec 3
            if ($response.paths.'\/planning\/staff-package' -or $response.paths.'/planning/staff-package') {
                return "http://127.0.0.1:$candidatePort"
            }
        } catch {
            continue
        }
    }

    return "http://127.0.0.1:8000"
}

$selectedPort = $Port
while (-not (Test-PortAvailable -CandidatePort $selectedPort) -and $selectedPort -lt ($Port + 20)) {
    $selectedPort++
}

if (-not (Test-PortAvailable -CandidatePort $selectedPort)) {
    throw "Could not find an open localhost port between $Port and $($Port + 20)."
}

$resolvedBackendUrl = Resolve-BackendUrl -PreferredUrl $BackendUrl
$env:SMCR_STAFF_AI_BACKEND_URL = $resolvedBackendUrl

$existing = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match "uvicorn chatgpt_app\.main:app" } |
    Select-Object -First 1

if ($existing) {
    Write-Host ""
    Write-Host "An SMCR ChatGPT app process is already running." -ForegroundColor Yellow
    Write-Host "PID: $($existing.ProcessId)" -ForegroundColor DarkGray
    Write-Host "Command: $($existing.CommandLine)" -ForegroundColor DarkGray
    Write-Host ""
}

Write-Host ""
Write-Host "Starting SMCR ChatGPT app surface..." -ForegroundColor Cyan
Write-Host "Repo: $repoRoot" -ForegroundColor DarkGray
Write-Host "Backend URL: $resolvedBackendUrl" -ForegroundColor DarkGray
Write-Host "Local MCP URL: http://127.0.0.1:$selectedPort/mcp" -ForegroundColor DarkGray
Write-Host ""

$arguments = @("-m", "uvicorn", "chatgpt_app.main:app", "--host", "127.0.0.1", "--port", "$selectedPort")

if ($Detached) {
    $process = Start-Process python -ArgumentList $arguments -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
    Write-Host "Started detached app server PID $($process.Id)." -ForegroundColor Green
} else {
    python @arguments
}
