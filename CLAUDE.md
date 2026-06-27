# SMCR Staff AI — AI Assistant Context

This file is read automatically by Claude Code and compatible AI assistants.
It tells your AI how to help you use and develop this project.

---

## What This Is

A local-first command-post dashboard for USMC reserve staff officers. Runs on your
machine — no cloud calls at runtime. The AI assistant (you, reading this) is the
reasoning layer; the app provides structure, continuity storage, and workflow scaffolds.

Five lanes: **Overview** · **Watch** · **Bench+Files** · **Workflows** · **Workspace**

---

## Starting the Server

```bash
# Windows
start.bat

# Mac / Linux
./start.sh

# Docker (any platform)
docker compose up
```

Server runs at **http://localhost:8000** — dashboard at **http://localhost:8000/dashboard**

The first time you open the dashboard, a profile ID is generated automatically and your
workspace loads. No account creation required.

---

## Helping a New User

If someone just cloned this repo and opened you (the AI assistant), do this:

1. **Start the server** — run `start.bat` (Windows) or `./start.sh` (Mac/Linux) in a terminal
2. **Open the dashboard** — http://localhost:8000/dashboard
3. **Workspace auto-loads** — profile ID is generated on first visit, stored in the browser
4. **Set up their profile** — Workspace tab → Profile & preferences → fill in billet, unit, MOS
5. **Load module packs** — Bench+Files lane → Module Packs → activate any packs in `modules/`

---

## Key Architecture Facts

- **Stack:** FastAPI + vanilla JS SPA. No framework on the frontend. Python 3.12, `uv` for deps.
- **Storage:** All user state is flat JSON files under `%LOCALAPPDATA%\smcr-staff-ai\` (or `$SMCR_STAFF_AI_HOME`). Pattern: `SHA256(user_key)[:24].json` per domain.
- **No LLM at runtime.** Advisory text comes from static lookups and templates. Connect your AI to the *repo* for reasoning, not to the running server.
- **Auth:** Optional passkey via `X-Local-API-Key` header. Unset = no gate (fine for single-user local use).
- **Routes:** `app/api/routes/` — each file is one domain. `app/main.py` registers all of them.
- **Dashboard JS:** `app/static/dashboard/dashboard.js` — single file, function-based, no bundler.

---

## Security Constraints (non-negotiable)

- **UNCLASSIFIED only.** Do not add, suggest, or process: classified info, CUI, COMSEC, real
  frequencies, call signs, precise unit movements, sensitive operational details, or unnecessary PII.
- All outputs are **advisory drafts** — human review required before acting on anything.
- Do not install, delete, promote, sync, or rewrite skills or hooks unless explicitly asked.

---

## Running Tests

```bash
uv run pytest tests/ -q          # unit + integration
uv run mypy app tests            # type checks
uv run ruff check .              # lint
```

---

## Module Packs

Drop a folder into `modules/` to create a pack. The folder can contain `.md`, `.txt`, or `.pdf`
files plus an optional `manifest.json` and `smcr-profile.json` (seeds profile defaults on activation).

```
modules/
  my-unit-pack/
    manifest.json          # { "title": "...", "description": "..." }
    smcr-profile.json      # { "billet": "S-3", "unit": "...", "mos": "..." }
    battle-rhythm.md
    contact-list.md
```

Activate in the dashboard → Bench+Files → Module Packs → Activate.

---

## Saving User Work Products (for AI assistants helping a user)

When a user asks you to generate, save, or organize documents, scenario files, exercise
products, or any work output — **always save to the `projects/` directory** in the repo root.
Never save user artifacts into the app source tree, `.claude/`, `docs/`, or temp directories.

### Folder structure

```
projects/
  {project-name}/              # kebab-case, descriptive (e.g., "cax-23-taiwan-strait")
    README.md                  # Project purpose, dates, participants, status
    scenario/                  # Scenario-specific content (MSEL, injects, background)
    products/                  # Staff products (OPORDs, FRAGOs, AARs, briefs)
    references/                # Maps, source docs, doctrine extracts
    notes/                     # Working notes, session logs, AI-generated analysis
```

### Rules

- **One folder per project.** Don't dump files loose in `projects/`.
- **Create the project folder and README.md on first save.** Ask the user for a project name
  if they haven't specified one.
- **Use clear filenames.** `opord-phase-1-draft.md` not `output.md`. Include dates where
  useful: `aar-20260626.md`.
- **The `projects/` directory is gitignored.** User work products never get committed to the
  public repo. This is intentional — scenario content may contain exercise-specific details.
- **Storage path on disk:** The app also provisions a `projects/` folder under the user's
  local data directory (`%LOCALAPPDATA%\smcr-staff-ai\projects\` on Windows). The repo-local
  `projects/` folder is the preferred location when working from the repo; the app-data path
  is used by the running server.
- **UNCLASSIFIED only** — the security constraint applies to project files too.

---

## Common Tasks for Developers

| Task | Command / File |
|---|---|
| Add a new API route | Create `app/api/routes/foo.py`, register in `app/main.py` |
| Add a new schema | `app/schemas/foo.py` (Pydantic BaseModel) |
| Add a new store | Follow pattern in `app/services/staff/bench_sections_store.py` |
| Add a new dashboard widget | Edit `app/static/dashboard/index.html` + `dashboard.js` |
| Change storage paths | `app/core/config.py` → add `default_*_dir()` + field in `Settings` |
