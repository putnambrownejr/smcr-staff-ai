@echo off
REM smcr-staff-ai — one-command start for Windows
REM Requires: Python 3.12+ and uv  (https://docs.astral.sh/uv/getting-started/installation/)

cd /d "%~dp0"

if not defined SMCR_PORT set "SMCR_PORT=8000"

where uv >nul 2>&1
if errorlevel 1 (
    echo uv not found. Install it from https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo Installing / syncing dependencies...
uv sync --frozen
if errorlevel 1 exit /b 1

uv run python -m app.startup_preflight --port "%SMCR_PORT%"
if errorlevel 1 exit /b 1

echo.
echo Starting smcr-staff-ai at http://localhost:%SMCR_PORT%
echo Press Ctrl+C to stop.
echo.

uv run uvicorn app.main:app --host 127.0.0.1 --port "%SMCR_PORT%" --reload
