# SMCR Staff AI — AI Assistant Instructions

**Read this file first.** It applies to every AI assistant working with this repo —
Claude, Codex, Gemini, Copilot, Cursor, or any other tool. Tool-specific files
(CLAUDE.md, CODEX.md, etc.) extend these rules but do not override them.

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

---

## Security Constraints (non-negotiable)

- **UNCLASSIFIED only.** Do not add, suggest, or process: classified info, CUI, COMSEC, real
  frequencies, call signs, precise unit movements, sensitive operational details, or unnecessary PII.
- All outputs are **advisory drafts** — human review required before acting on anything.
- Do not install, delete, promote, sync, or rewrite skills or hooks unless explicitly asked.

---

## Source Citation and Accuracy (non-negotiable)

This project stores doctrinal references, organizational structures, and interagency
knowledge that can go stale. Treat every stored fact as **"true when last checked"**, not
as current truth.

- **Cite sources explicitly.** Every claim about doctrine, policy, organizational structure,
  or procedure must name the source (publication number, website, order). "Per JP 3-29" not
  "doctrinally." If you can't name the source, say so.
- **Date your knowledge.** When referencing stored facts (e.g., "DoS/BHR is the lead
  humanitarian agency"), state when this was last verified: "as of [date]."
- **Warn on every output.** Every product, brief, or advisory must include a footer:
  `DRAFT — Verify all references against current official sources before acting.`
- **Flag uncertainty.** If a fact could have changed since last verification (org structures,
  personnel, policy, funding status), say "confirm current status" rather than stating it flat.
- **Don't present AI memory as ground truth.** Stored project knowledge, instruction files,
  and agent system prompts are starting points for research, not finished answers.
- **Prefer live sources.** When the user has access to current references (MOL, official
  orders, unit SOPs), defer to those over stored knowledge.

---

## Saving User Work Products

When generating documents, scenario files, exercise products, rosters, briefs, or any
work output — **always save to `projects/` in the repo root.** Never save user artifacts
into the app source tree, `.claude/`, `docs/`, `tools/`, or temp directories.

### Folder structure

```
projects/
  {project-name}/              # kebab-case, descriptive (e.g., "ven-fhadr-jun26")
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
- **Use clear filenames** with dates: `ca-brief-20260626.md`, not `output.md`.
- **Always produce dual-format outputs.** Every staff product gets both:
  - `.md` (readable, diffable, versionable)
  - `.docx` (distributable, printable, email-ready)
  - For tabular data: `.csv` (Excel-importable) alongside any `.md` table
- **Write a session log** (`session-log-YYYYMMDD.md`) for each working session summarizing
  what was produced, inputs used, corrections applied, and outstanding gaps.
- **The `projects/` directory is gitignored.** User work products never get committed to the
  public repo. This is intentional — scenario content may contain exercise-specific details.
- **Storage path on disk:** The app also provisions a `projects/` folder under the user's
  local data directory (`%LOCALAPPDATA%\smcr-staff-ai\projects\` on Windows). The repo-local
  `projects/` folder is the preferred location when working from the repo; the app-data path
  is used by the running server.
- **UNCLASSIFIED only** — the security constraint applies to project files too.

---

## Interagency Knowledge (current as of 2026)

These standing facts apply to all FHADR, interagency, and humanitarian planning work.
**Verify currency before using in products** — these can change.

- **USAID no longer exists** (dissolved 2025). Humanitarian coordination functions
  transferred to the **Department of State Bureau of Humanitarian Assistance (DoS/BHR)**.
- **JP 3-29** (Foreign Humanitarian Assistance) is in revision. Use the current edition but
  **substitute DoS/BHR wherever USAID/BHA appears**.
- The **DART** (Disaster Assistance Response Team) concept may continue under DoS/BHR as a
  "forward coordination team" — confirm current terminology before using in products.
- Do not reference USAID, USAID/OFDA, or USAID/BHA as active organizations in any product.
  Historical references (e.g., "formerly USAID/BHA, now DoS/BHR") are acceptable for context.

---

## Key Architecture Facts

- **Stack:** FastAPI + vanilla JS SPA. No framework on the frontend. Python 3.12, `uv` for deps.
- **Storage:** All user state is flat JSON files under `%LOCALAPPDATA%\smcr-staff-ai\` (or
  `$SMCR_STAFF_AI_HOME`). Pattern: `SHA256(user_key)[:24].json` per domain.
- **No LLM at runtime.** Advisory text comes from static lookups and templates. Connect your
  AI to the *repo* for reasoning, not to the running server.
- **Auth:** Optional passkey via `X-Local-API-Key` header. Unset = no gate (fine for
  single-user local use).
- **Routes:** `app/api/routes/` — each file is one domain. `app/main.py` registers all of them.
- **Dashboard JS:** `app/static/dashboard/dashboard.js` — single file, function-based, no bundler.

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

## Common Tasks for Developers

| Task | Command / File |
|---|---|
| Add a new API route | Create `app/api/routes/foo.py`, register in `app/main.py` |
| Add a new schema | `app/schemas/foo.py` (Pydantic BaseModel) |
| Add a new store | Follow pattern in `app/services/staff/bench_sections_store.py` |
| Add a new dashboard widget | Edit `app/static/dashboard/index.html` + `dashboard.js` |
| Change storage paths | `app/core/config.py` → add `default_*_dir()` + field in `Settings` |
