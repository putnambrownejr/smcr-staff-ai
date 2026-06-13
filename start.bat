@echo off
REM smcr-staff-ai — one-command start for Windows
REM Requires: Python 3.12+ and uv  (https://docs.astral.sh/uv/getting-started/installation/)

cd /d "%~dp0"

where uv >nul 2>&1
if errorlevel 1 (
    echo uv not found. Install it from https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo Installing / syncing dependencies...
uv sync --frozen

echo.
echo Starting smcr-staff-ai at http://localhost:8000
echo Press Ctrl+C to stop.
echo.

uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
