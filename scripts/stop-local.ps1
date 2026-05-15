param(
    [switch]$WithPostgres
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$composeArgs = @("compose")
if ($WithPostgres) {
    $composeArgs += @("--profile", "postgres")
}
$composeArgs += @("down")

Write-Host ""
Write-Host "Stopping SMCR Staff AI local Docker stack..." -ForegroundColor Yellow
Write-Host "Repo: $repoRoot" -ForegroundColor DarkGray
Write-Host ""

docker @composeArgs
