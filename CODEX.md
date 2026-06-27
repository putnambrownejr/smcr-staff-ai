# SMCR Staff AI — OpenAI Codex Context

**Read [AGENTS.md](AGENTS.md) first.** It contains the shared rules for all AI assistants
(security, source citation, project save paths, interagency knowledge, architecture).
Everything below is Codex-specific and extends those rules.

---

## Environment

- **Python 3.12**, managed with `uv` (not pip/poetry).
- Run tests: `uv run pytest tests/ -q`
- Type check: `uv run mypy app tests`
- Lint: `uv run ruff check .`
- Start server: `start.bat` (Windows) or `./start.sh` (Mac/Linux)

## Code Conventions

- FastAPI routes in `app/api/routes/`, registered in `app/main.py`.
- Pydantic models in `app/schemas/`.
- Agent pattern: class extends `Agent` base in `app/services/agents/base.py`,
  registered via builder function in `app/services/agents/registry.py`.
- Frontend is vanilla JS in `app/static/dashboard/` — no framework, no bundler.
- Storage is flat JSON files, not a database.
