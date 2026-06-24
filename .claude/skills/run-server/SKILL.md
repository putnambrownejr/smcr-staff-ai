---
name: run-server
description: Start the smcr-staff-ai dev server (FastAPI + uvicorn on port 8000), wait for healthy, and optionally open the dashboard. Use when the user says "start the server", "run the app", or when another skill needs the server running.
---

# Run Server — smcr-staff-ai

## Purpose

Standardized way to start the dev server. Other skills (like `verifier-dashboard`) call this as their setup step. The bundled `/run` skill looks for `run-*` skills in `.claude/skills/`.

## Quick Start

### Windows (PowerShell)

```powershell
# From the project root
uv sync --frozen && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Or use the launcher script:
```powershell
.\start.bat
```

### macOS / Linux (Bash)

```bash
uv sync --frozen && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Or use the launcher script:
```bash
./start.sh
```

### Docker

```bash
docker compose up
```

## Health Check

Wait for the server to be ready before proceeding:

```bash
# Bash — poll until healthy (max 30s)
for i in $(seq 1 30); do
  curl -sf http://localhost:8000/health && echo " Server ready" && break
  sleep 1
done
```

```powershell
# PowerShell — poll until healthy (max 30s)
1..30 | ForEach-Object {
  try {
    $r = Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing -ErrorAction Stop
    if ($r.StatusCode -eq 200) { Write-Host "Server ready"; break }
  } catch { Start-Sleep 1 }
}
```

Expected response: `{"status": "ok"}`

## Endpoints

| Endpoint | Purpose |
|---|---|
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/dashboard` | Main dashboard SPA |
| `http://localhost:8000/docs` | FastAPI auto-generated API docs (Swagger UI) |
| `http://localhost:8000/redoc` | ReDoc API docs |

## Running in Background

When another skill needs the server running but doesn't want to block:

```bash
# Bash — background with PID capture
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
SERVER_PID=$!
```

```powershell
# PowerShell — background job
$job = Start-Job { Set-Location C:\smcr-staff-ai; uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload }
```

## Port Conflict

If port 8000 is already in use:

```bash
# Check what's using it
lsof -i :8000  # macOS/Linux
```

```powershell
# PowerShell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { Get-Process -Id $_.OwningProcess }
```

If it's a stale server from a previous session, kill it and restart. If it's something else, pick a different port with `--port 8001`.

## Shutdown

```bash
# If backgrounded
kill $SERVER_PID

# By port
lsof -ti:8000 | xargs kill 2>/dev/null
```

```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
```

## Prerequisites

- Python 3.12+
- `uv` package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- No other dependencies — `uv sync --frozen` handles everything from `uv.lock`
