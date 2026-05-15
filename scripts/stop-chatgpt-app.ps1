param()

$ErrorActionPreference = "Stop"

$processes = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match "uvicorn chatgpt_app\.main:app" }

if (-not $processes) {
    Write-Host ""
    Write-Host "No SMCR ChatGPT app server process found." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "Stopping SMCR ChatGPT app surface..." -ForegroundColor Yellow
Write-Host ""

foreach ($process in $processes) {
    Write-Host "Stopping PID $($process.ProcessId)" -ForegroundColor DarkGray
    Stop-Process -Id $process.ProcessId -Force
}
