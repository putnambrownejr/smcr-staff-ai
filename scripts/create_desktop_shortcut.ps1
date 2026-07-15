# Installs (or removes) the SMCR Staff AI desktop shortcut and login
# auto-start, so the dashboard can be opened without going through an AI
# assistant. Safe to re-run -- shortcuts are overwritten, not duplicated.
#
# Default (no switches): installs everything --
#   - Desktop: "SMCR Staff AI.lnk" -> opens the dashboard (starts the server
#     first if it isn't already running). Shutting down happens INSIDE the
#     dashboard: the power button in the top bar. One icon, whole lifecycle.
#   - Startup folder: silently starts the server when you log in (no browser
#     tab pops open on its own -- the desktop icon is your "take me there")
#
# Earlier versions also installed a "Stop SMCR Staff AI" desktop icon; the
# in-dash power button replaced it, and installing now removes the old icon.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\create_desktop_shortcut.ps1
#   ... -NoAutostart      # desktop icon only, skip login auto-start
#   ... -NoDesktop        # auto-start only, skip the desktop icon
#   ... -RemoveAll        # undo everything this script has installed
#   ... -RemoveDesktop    # remove just the desktop icon
#   ... -RemoveAutostart  # remove just the login auto-start

param(
    [switch]$NoDesktop,
    [switch]$NoAutostart,
    [switch]$RemoveDesktop,
    [switch]$RemoveAutostart,
    [switch]$RemoveAll
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonwExe = Join-Path $RepoRoot ".venv\Scripts\pythonw.exe"
$IconPath = Join-Path $RepoRoot "scripts\assets\smcr-staff-ai.ico"
$LaunchScript = Join-Path $RepoRoot "scripts\launch_dashboard.pyw"
$AutostartScript = Join-Path $RepoRoot "scripts\start_server_hidden.pyw"

$DesktopDir = [Environment]::GetFolderPath("Desktop")
$StartupDir = [Environment]::GetFolderPath("Startup")
$OpenShortcut = Join-Path $DesktopDir "SMCR Staff AI.lnk"
$StopShortcut = Join-Path $DesktopDir "Stop SMCR Staff AI.lnk"
$AutostartShortcut = Join-Path $StartupDir "SMCR Staff AI (autostart).lnk"

function New-AppShortcut {
    param([string]$Path, [string]$Arguments, [string]$Description)
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $PythonwExe
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = $RepoRoot
    $shortcut.Description = $Description
    if (Test-Path $IconPath) {
        $shortcut.IconLocation = $IconPath
    }
    $shortcut.Save()
}

function Remove-IfExists {
    param([string]$Path)
    if (Test-Path $Path) {
        Remove-Item $Path -Force
        Write-Output "Removed: $Path"
    }
}

if ($RemoveAll -or $RemoveDesktop) {
    Remove-IfExists $OpenShortcut
    Remove-IfExists $StopShortcut
}
if ($RemoveAll -or $RemoveAutostart) {
    Remove-IfExists $AutostartShortcut
}
if ($RemoveAll -or $RemoveDesktop -or $RemoveAutostart) {
    exit 0
}

if (-not (Test-Path $PythonwExe)) {
    Write-Output "SMCR Staff AI isn't set up yet on this machine."
    Write-Output "Run start.bat once first, then re-run this script."
    exit 1
}

if (-not $NoDesktop) {
    New-AppShortcut -Path $OpenShortcut -Arguments "`"$LaunchScript`"" `
        -Description "Open the SMCR Staff AI dashboard (starts it first if needed)"
    # The in-dash power button replaced the separate Stop icon; clean up any
    # copy an earlier version of this script installed.
    Remove-IfExists $StopShortcut
    Write-Output "Desktop shortcut created:"
    Write-Output "  $OpenShortcut"
    Write-Output "  (shut down from inside the dashboard: the power button in the top bar)"
}

if (-not $NoAutostart) {
    New-AppShortcut -Path $AutostartShortcut -Arguments "`"$AutostartScript`"" `
        -Description "Silently starts the SMCR Staff AI server at login (no browser tab)"
    Write-Output "Login auto-start enabled:"
    Write-Output "  $AutostartShortcut"
}

Write-Output ""
Write-Output "Double-click ""SMCR Staff AI"" on the desktop anytime to open the dashboard."
Write-Output "To undo: re-run this script with -RemoveAll"
