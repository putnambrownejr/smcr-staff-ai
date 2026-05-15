param(
    [switch]$Detached,
    [switch]$OpenBrowser,
    [switch]$WithPostgres,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

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

$selectedPort = $Port
while (-not (Test-PortAvailable -CandidatePort $selectedPort) -and $selectedPort -lt ($Port + 20)) {
    $selectedPort++
}

if (-not (Test-PortAvailable -CandidatePort $selectedPort)) {
    throw "Could not find an open localhost port between $Port and $($Port + 20)."
}

$env:LOCAL_BIND_PORT = "$selectedPort"

$composeArgs = @("compose")
if ($WithPostgres) {
    $composeArgs += @("--profile", "postgres")
}

if ($Detached) {
    $composeArgs += @("up", "--build", "-d")
} else {
    $composeArgs += @("up", "--build")
}

Write-Host ""
Write-Host "Starting SMCR Staff AI local Docker stack..." -ForegroundColor Cyan
Write-Host "Repo: $repoRoot" -ForegroundColor DarkGray
Write-Host "Local URL: http://127.0.0.1:$selectedPort/dashboard" -ForegroundColor DarkGray
Write-Host ""

if ($OpenBrowser -and $Detached) {
    $browserUrl = "http://127.0.0.1:$selectedPort/dashboard"
    $job = Start-Job -ScriptBlock {
        param($Url)
        Start-Sleep -Seconds 6
        Start-Process $Url
    } -ArgumentList $browserUrl
    $null = $job
}

docker @composeArgs
