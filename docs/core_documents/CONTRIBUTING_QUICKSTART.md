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
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -e ".[dev]"
python -m pytest tests/ -q    # all tests should pass
uvicorn app.main:app --reload  # starts at http://localhost:8000
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
  db/               SQLModel models and session

docs/
  agents_setup/     agent catalog and design notes
  core_documents/   project purpose, roadmap, architecture
  sources/          doctrine and reference notes (feed the reference library)
  compatibility/    how AI tools should read and use this repo

skills/             operator-facing skill overlays (SKILL.md files)
data/seed/          example seed data for first-run experience
tests/              Offline tests — run before every commit
```

---

## Where To Start By Contribution Type

### Adding a new agent
1. Read `app/services/agents/base.py` — all agents extend `Agent`
2. Copy the pattern from any existing agent (e.g., `app/services/agents/s3_opso_agent.py`)
3. Register it in `app/services/agents/registry.py`
4. Add a test in `tests/` following `tests/test_agent_registry.py`

### Adding a new route
1. Add schema to `app/schemas/` (Pydantic model)
2. Add service logic to `app/services/`
3. Add route to `app/api/routes/` and register in `app/main.py`
4. Add auth guard: `dependencies=[LocalApiKeyDependency]` on the router
5. Add test following any existing route test pattern
6. Consider adding a `/demo/*` equivalent for stateless access

### Adding a skill
1. Create `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`)
2. Point to existing routes rather than inventing new logic
3. Update `skills/README.md`

### Updating docs/sources
Files in `docs/sources/` feed the dashboard reference library automatically.
Use the format in any existing file: `# Title`, `## Primary Sources`, `## Expected Uses`, `## Notes`.

---

## What Not To Build

The repo already has opinions on this — see `docs/core_documents/capability_reuse_audit.md`.

Short version:
- **Do not** rebuild OAuth, email auth, or calendar connector auth — use the stub interfaces
- **Do not** add more specialist agents until packaging and discoverability improve
- **Do not** break the local-first, UNCLASSIFIED-only posture
- **Do not** store user context (handoffs, uploads, API keys) in the repo

---

## Before You Commit

```bash
python -m pytest tests/ -q         # all tests must pass
python -m ruff check app/ tests/   # lint
python -m mypy app/                # type check (strict)
```

CI enforces: **all tests passing, mypy clean** (`.github/workflows/ci.yml`).
Ruff is a recommended local check — run it before committing, but it is not yet
a CI gate and the existing tree still has lint debt to clear.

---

## Key Files For Orientation

| File | What it tells you |
|---|---|
| `app/main.py` | All routers registered here — the full route surface |
| `app/services/agents/registry.py` | Every agent, its ID, and description |
| `docs/core_documents/project_purpose.md` | Why this exists and who it's for |
| `docs/core_documents/workflow_map.md` | How routes combine into real workflows |
| `docs/agents_setup/AGENTS.md` | Agent design philosophy |
| `data/seed/` | Example data shapes for every major entity |
| `docs/examples/` | Canonical request/response examples |

---

## Getting Help

- `README.md` — full feature reference
- `http://localhost:8000/docs` — live OpenAPI with try-it-out
- `docs/compatibility/ai_assistant_guide.md` — how to use an AI tool with this repo
