# Gemini Code Assist — SMCR Staff AI

**Read [AGENTS.md](../AGENTS.md) first.** It contains the shared rules for all AI
assistants working with this repo: security constraints, source citation requirements,
project save paths, dual-format output rules, and interagency knowledge.

## Quick reference

- **Python 3.12**, managed with `uv`. Run tests: `uv run pytest tests/ -q`
- FastAPI routes in `app/api/routes/`, registered in `app/main.py`
- Pydantic models in `app/schemas/`
- Agent pattern: class extends `Agent` in `app/services/agents/base.py`,
  registered via builder function in `app/services/agents/registry.py`
- Frontend is vanilla JS in `app/static/dashboard/` — no framework, no bundler
- Storage is flat JSON files under `%LOCALAPPDATA%\smcr-staff-ai\`, not a database
- Save user work products to `projects/` — never into the app source tree
- **UNCLASSIFIED only** — no classified, CUI, COMSEC, PII, or sensitive operational details
- All outputs are advisory drafts — cite sources, date knowledge, flag uncertainty
