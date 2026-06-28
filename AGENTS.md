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

## Startup Wizard (New User Onboarding)

If the user says "boot the startup wizard", "startup wizard", "getting started",
"I'm new", "help me set up", or anything similar — they are a new user who just
downloaded this repo and needs to be walked through setup. Do this:

1. **Welcome them.** Explain what this project is in plain language: an AI tool for
   reserve Marines that helps with staff products, admin, training, and doctrine.
2. **Ask about their situation:** rank, MOS, billet, what kind of help they need.
3. **Check if the server can run.** Ask them to try:
   - Windows: `start.bat`
   - Mac/Linux: `./start.sh`
   - If Python/uv errors → help them install Python 3.12+ from python.org (remind
     them to check "Add to PATH" on Windows) and uv via `pip install uv`.
   - If they can't install Python (government computer, permissions), skip the
     server — the AI assistant (you) still works without it.
4. **If the server starts:** direct them to http://localhost:8000/dashboard and walk
   them through: Workspace tab → Profile & preferences → fill in rank, MOS, billet,
   unit. Then show them the five lanes (Overview, Watch, Bench+Files, Workflows,
   Workspace).
5. **Regardless of server:** tell them they can ask you questions right now. Give
   them 2-3 starter prompts based on what they said their billet/needs are.
6. **Set expectations:** UNCLASSIFIED only, everything is a draft requiring human
   review, AI doesn't access DoD systems, verify cited regulations are current.

Tone: direct, practical, no AI jargon. Talk like a helpful Staff NCO walking
someone through a new system.

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

## Interagency Knowledge (current as of mid-2026)

These standing facts apply to all FHADR, interagency, and humanitarian planning work.
**Verify currency before using in products** — these can change.

### USAID Dissolution and State Department Reorganization

- **USAID no longer exists as an independent agency** (dissolved 2025). Executive Orders
  14150 and 14169 (Jan 20, 2025) froze most foreign assistance. Secretary Rubio absorbed
  USAID functions into State by July 1, 2025. Legislative abolition is pending but USAID
  is operationally defunct.
- Do not reference USAID, USAID/OFDA, or USAID/BHA as active organizations in any product.
  Historical references (e.g., "formerly USAID/BHA") are acceptable for context.

### New State Department Structure (Apr 2025 Reorg)

The chain of command for overseas aid is now:
**President → Secretary of State → Under Secretary for Foreign Assistance & Humanitarian
Affairs ("F") → State's humanitarian and regional bureaus.**

Key bureaus under the new Under Secretary "F":

| Bureau | Former Home | Function |
|---|---|---|
| Bureau for Humanitarian Assistance | USAID/BHA | Food, water, shelter, emergency medical, nutrition |
| Bureau of Global Health Security & Diplomacy | USAID/Bureau for Global Health | HIV/AIDS, malaria, maternal/child health, PEPFAR |
| Bureau of Disaster & Humanitarian Response (BDHR) | USAID/OFDA (new, proposed 2026) | Consolidates emergency relief; will house DART-equivalent |
| Bureau of Population, Refugees & Migration (PRM) | State/PRM (unchanged) | Refugee resettlement, migration |
| Bureau of Democracy, Human Rights & Religious Freedom (DRL) | State/DRL + USAID/DRG | Democracy, human rights (renamed to include "Religious Freedom") |

Other transfers:
- **Food for Peace (Title II)** → USDA (not State)
- **Regional development** → State's geographic bureaus (AFR, EAP, EUR, NEA, WHA)
- **Education/cultural exchange** → State's Bureau of Educational & Cultural Affairs (ECA)
- **Development finance** → U.S. International Development Finance Corporation (DFC)

### DART Status

- All four active DARTs (Afghanistan, Gaza, Sudan, Ukraine) ceased normal operations
  in Feb 2025 when USAID staff were placed on leave.
- BHA staff was cut from ~1,300 to ~50 people embedded in PRM by July 2025.
- DART capability is effectively shelved. State's proposed BDHR (2026) would rebuild
  DART-equivalent functions under a Senate-confirmed Assistant Secretary.
- In the interim, **DoD assets fill the gap**: military transport (C-17s, helicopters,
  ships) and Civil Affairs units (Army/Marines) provide disaster response capacity.
- **JP 3-29** and **JP 3-57** still identify USAID/OFDA as the U.S. lead for foreign
  disaster relief — these are pending doctrinal update. Substitute State's humanitarian
  bureau (or future BDHR) wherever USAID/BHA or USAID/OFDA appears.

### Civil-Military Coordination (Post-Reorg)

- The **Country Team** framework at each embassy remains the primary coordination
  mechanism. State officials now wear the "aid hat" that USAID personnel held.
- DoD Combatant Commands still coordinate via embassy liaison, but the civilian
  counterpart is now State's humanitarian bureau, not USAID.
- USAID's Office of Civilian-Military Coordination (CMC) — which embedded officers
  in each combatant command — will transition to State's responsibility.
- Civil Affairs units (Army/Marine Corps) continue to embed with civilian agencies.
- Coordination mechanisms remain: Country Team Disaster Relief Coordination Committees,
  Defense Attachés, OCHA liaison, joint planning boards.
- Experts warn U.S. disaster response capability has been "fundamentally truncated"
  by staff cuts — military planners should factor in degraded civilian capacity.

### Budget Impact

- U.S. historically provided ~43% of global humanitarian funding.
- FY2026 budget request cuts humanitarian funding by roughly two-thirds
  (~$2.5B combined IDA+MRA, down from ~$9.9B in FY2023).
- This affects planning assumptions for FHADR exercises and real-world operations.

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
