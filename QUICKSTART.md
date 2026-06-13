# Quickstart

SMCR Staff AI is a local command-post dashboard for USMC reserve staff workflows — session handoffs, watch feeds, bench notebooks, planning tools, and more. It runs entirely on your machine; no cloud dependency is required at runtime.

## Prerequisites

- Python 3.12+
- `uv` — install with `pip install uv`

## Running the App

```bash
# 1. Install dependencies
uv sync --frozen

# 2. Configure environment
cp .env.example .env
# Edit .env: set LOCAL_API_KEY to any string you choose (used to gate the local API)

# 3. Start the server
uv run uvicorn app.main:app --reload

# 4. Open the dashboard
#    http://localhost:8000/static/dashboard/index.html
#
#    Enter your LOCAL_API_KEY on the landing screen, then click "Open demo workspace"
#    to explore without loading real data.
```

## Five Lanes

| Lane | Purpose |
|------|---------|
| **Overview** | Readiness posture, Act Now queue, history fact, command-post summary |
| **Watch** | MARADMIN feed, source watch, reading tracker |
| **Bench + Files** | Section bench notebook (configurable), uploaded context files |
| **Workflows** | Staff product scaffolds and planning-cell tools |
| **Workspace** | Load/save named workspaces; session handoff notes |

## Running Tests

```bash
uv run pytest tests/ -q          # unit + integration (E2E skipped by default)
uv run pytest -m e2e tests/e2e/  # E2E (requires: playwright install chromium + running server)
```
