# Contributing Quickstart

Everything you need to make a meaningful change to `smcr-staff-ai` in under 15 minutes.

---

## What This Is

A local-first advisory toolkit for SMCR staff workflows. It runs on your machine.
No cloud infrastructure, no auth tokens required to get started.
All outputs are advisory drafts — human review required before acting on anything.

---

## First Run

```bash
git clone https://github.com/putnambrownejr/smcr-staff-ai
cd smcr-staff-ai

# Windows
start.bat

# Mac / Linux
./start.sh

# Or manually:
uv sync --frozen --extra dev
uv run pytest tests/ -q            # all tests should pass
uv run uvicorn app.main:app --reload  # starts at http://localhost:8000
```

Open the dashboard: **http://localhost:8000/dashboard**
Browse the API: **http://localhost:8000/docs**

---

## Project Layout

```
app/
  api/routes/       FastAPI routes — this is the public surface
  services/         business logic, agents, ingestion, storage
  schemas/          Pydantic models — source of truth for data shapes
  static/dashboard/ single-file dashboard (HTML + JS + CSS)
  core/             auth, config, security, logging

docs/
  core_documents/   project purpose, roadmap, architecture
  sources/          doctrine and reference notes (feed the reference library)
  compatibility/    how AI tools should read and use this repo

data/seed/          example seed data for first-run experience
tests/              Offline tests — run before every commit
```

---

## Where To Start By Contribution Type

### Adding a new agent
See [docs/contributing-agents.md](../contributing-agents.md) for the full checklist.

### Adding a new route
1. Add schema to `app/schemas/` (Pydantic model)
2. Add service logic to `app/services/`
3. Add route to `app/api/routes/` and register in `app/main.py`
4. Add auth guard: `dependencies=[LocalApiKeyDependency]` on the router
5. Add test following any existing route test pattern
6. Consider adding a `/demo/*` equivalent for stateless access

### Updating docs/sources
Files in `docs/sources/` feed the reference library.
Use the format in any existing file: `# Title`, `## Primary Sources`, `## Expected Uses`, `## Notes`.

---

## What Not To Build

See `docs/core_documents/capability_reuse_audit.md` for the full policy.

Short version:
- **Do not** rebuild OAuth, email auth, or calendar connector auth — use the stub interfaces
- **Do not** break the local-first, UNCLASSIFIED-only posture
- **Do not** store user context (handoffs, uploads, API keys) in the repo

---

## Before You Commit

```bash
uv run pytest tests/ -q       # all tests must pass
uv run ruff check .            # lint
uv run mypy app tests          # type check
```

CI enforces all three (`.github/workflows/ci.yml`).

---

## Key Files For Orientation

| File | What it tells you |
|---|---|
| `app/main.py` | All routers registered here — the full route surface |
| `app/services/agents/registry.py` | Every agent, its ID, and description |
| `docs/core_documents/project_purpose.md` | Why this exists and who it's for |
| `docs/core_documents/workflow_map.md` | How routes combine into real workflows |
| `docs/contributing-agents.md` | Agent development guide |
| `data/seed/` | Example data shapes for every major entity |
| `docs/examples/` | Canonical request/response examples |

---

## Getting Help

- `README.md` — full feature reference
- `http://localhost:8000/docs` — live OpenAPI with try-it-out
- `docs/compatibility/ai_assistant_guide.md` — how to use an AI tool with this repo
