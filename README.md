# smcr-staff-ai

An UNCLASSIFIED, open-source FastAPI application for AI-enabled Selected Marine Corps Reserve staff workflows. Designed for SMCR officers and staff at company through division level who need advisory drafting support, public-source lookups, reserve administration helpers, and local context storage.

**This project is unofficial, not endorsed by the Marine Corps or Department of Defense, and not authoritative. All outputs are advisory drafts requiring human review.**

## How it works

The local app provides structured workflows, private storage, and advisory scaffolds — it does not call an LLM at runtime. The AI reasoning comes from your connected assistant (Claude, ChatGPT, Copilot, Gemini, etc.) reading the repo's patterns and responding with context-aware advice.

## Purpose

- **Build awareness** — surface what's due, what's changed, what needs attention
- **Hone the user's edge** — staff estimates, doctrine references, planning scaffolds
- **Reduce reserve-service friction** — DTS, FitReps, drill prep, admin workflows

See [docs/core_documents/project_purpose.md](docs/core_documents/project_purpose.md) for the full statement.

## Safety

Do not submit classified information, CUI, COMSEC, real frequencies, call signs, operational movement details, or unnecessary PII. The application includes runtime guardrails for sensitive inputs, but those checks do not replace human judgment.

## Prompt Packs — Use with Any AI (No Setup Required)

Don't want to install anything? Grab a **prompt pack** — copy-paste it into ChatGPT,
Claude, Gemini, or any AI chat and get Marine-specific guidance immediately.

| Pack | Who it's for |
|------|-------------|
| **Start here →** [Getting Started](prompt-packs/getting-started.md) | New to AI? This walks you through setup in 5 minutes |
| [General Marine](prompt-packs/general-marine.md) | Check-in, uniforms, drill prep, CAC/PKI, leadership |
| [Staff Products & Writing](prompt-packs/staff-products.md) | OPORDs, FRAGOs, SITREPs, AARs, briefs, ORM |
| [Training & Operations](prompt-packs/training-ops.md) | Planning (MCPP/R2P2), red-team, exercise design |
| [Reserve Admin](prompt-packs/reserve-admin.md) | DTS, MROWS, pay, FitReps, AT orders |

See the [prompt-packs/README.md](prompt-packs/README.md) for usage instructions.

## Quick start

**Prerequisites:** Python 3.12+, [uv](https://github.com/astral-sh/uv)

```bash
# Windows
start.bat

# Mac / Linux
./start.sh

# Docker
docker compose up
```

Then open:
- Dashboard: http://localhost:8000/dashboard
- API docs: http://localhost:8000/docs

See [QUICKSTART.md](QUICKSTART.md) for the full walkthrough.

## What's inside

### 37 advisory agents

21 standalone advisors + 16 echelon-adaptive staff archetypes. Each responds with structured advice, citations, confidence levels, and follow-up questions.

| Category | Examples |
|---|---|
| **Staff archetypes** | S-1 through G-9, XO, SgtMaj, SJA, PAO, Surgeon, Chaplain |
| **Standalone** | Planning Advisor, Staff Products, Drill Prep, Writing/Briefing, ORM, Red Team |
| **MAGTF elements** | ACE, GCE, LCE |
| **MOS-specific** | Infantry 03xx, Artillery 08xx, custom MOS recipes |

Staff archetypes adapt behavior based on echelon (platoon → division) — staff prefix, scope, product names, and coordination requirements all shift automatically.

### Staff Council

Runs all 16 staff archetypes in parallel for cross-lane deliberation on complex problems.

### Dashboard

Browser-based local operations board with five lanes:

- **Overview** — Act Now queue, readiness posture, onboarding
- **Watch** — MARADMIN feed, battle rhythm, message watch, custom RSS
- **Bench + Files** — Agent roster, module packs, local context, MOS recipes
- **Workflows** — Staff products, admin workflows, training scenarios, ORM
- **Workspace** — Profile, quick links, session handoff, settings

### Key features

- **Staff products** — OPORD, WARNO, FRAGO, SITREP, AAR, naval letter scaffolds
- **Admin workflows** — DTS, GTCC, awards, orders review checklists
- **Drill prep** — Date-to-tasks planner with .ics export
- **Session handoffs** — Persist context between drill weekends
- **Source watch** — MARADMIN RSS, NAVADMIN, DoD releases, custom feeds
- **Privacy sweep** — Pre-push review for PII/OPSEC leakage
- **PKI/CAC troubleshooting** — Advisory playbooks for common certificate issues
- **Career tracking** — PME gaps, FitRep reminders, billet discovery

## Architecture

- **Stack:** FastAPI + vanilla JS SPA. No frontend framework, no bundler.
- **Storage:** Flat JSON files under `%LOCALAPPDATA%\smcr-staff-ai\` (configurable via `$SMCR_STAFF_AI_HOME`)
- **No LLM at runtime.** Advisory text comes from static lookups and templates.
- **Auth:** Optional `X-Local-API-Key` header. Unset = no gate (fine for single-user local use).

```text
app/
  api/routes/          FastAPI endpoints
  core/                Settings, logging, guardrails
  schemas/             Pydantic request/response models
  services/
    agents/            Agent registry and 37 advisory agents
    admin/             Admin readiness and S-1 support
    calendar/          Drill-prep planner and calendar stubs
    career/            Career watch, PME, opportunities
    chief/             Chief/Aide orchestration brief
    ingestion/         RSS, MARADMIN, billet parsing
    rag/               Chunking/embedding interface stubs
    storage/           Local user-context storage
data/seed/             Example org, doctrine, and agent manifests
docs/                  Architecture, governance, roadmap
tests/                 477 offline fixture-based tests
```

## Development

```bash
uv run pytest tests/ -q       # unit + integration
uv run mypy app tests         # type checks
uv run ruff check .           # lint
```

See [docs/core_documents/CONTRIBUTING_QUICKSTART.md](docs/core_documents/CONTRIBUTING_QUICKSTART.md) for contributor setup.

## Connect your AI

[AGENTS.md](AGENTS.md) is the single instruction file for all AI assistants. It tells
your AI how to cite sources, where to save files, what security rules to follow, and
what interagency facts are current. Every tool-specific config file just points back to it.

### Code AI tools (auto-detected)

These tools read their instruction file automatically when you open the repo — no setup needed:

| Tool | Instruction file | Notes |
|---|---|---|
| Claude Code | [CLAUDE.md](CLAUDE.md) → AGENTS.md | Full agent/skill support |
| OpenAI Codex CLI | [CODEX.md](CODEX.md) → AGENTS.md | Use `codex` in repo root |
| GitHub Copilot | [.github/copilot-instructions.md](.github/copilot-instructions.md) → AGENTS.md | Works in VS Code / GitHub |
| Gemini Code Assist | [.gemini/styleguide.md](.gemini/styleguide.md) → AGENTS.md | Works in IDEs with Gemini plugin |

### Chat AIs (manual setup)

ChatGPT, Claude.ai, Gemini, and other chat-based AIs don't read repo files automatically.
You have two options:

**Option A — Paste at session start (quick, temporary)**

1. Open [AGENTS.md](AGENTS.md) and copy the full contents
2. Start a new chat session with your AI
3. Paste AGENTS.md as your first message, or upload it as a file
4. Say what you need — the AI will follow the rules for that session

This gives your AI the project's security rules, citation requirements, save paths, and
current interagency knowledge for one session. You'll need to paste it again next time.

**Option B — Save as a persistent project (recommended for regular use)**

| Platform | How to set up |
|---|---|
| **Claude.ai** | Create a Project → paste AGENTS.md into Project Instructions |
| **ChatGPT** | Create a Custom GPT → paste AGENTS.md into Instructions |
| **Gemini** | Create a Gem → paste AGENTS.md into the system prompt |

This makes the rules permanent — every conversation in that project/GPT/Gem follows them
automatically.

### What AGENTS.md gives your AI

When loaded, your AI will automatically:

- **Save files** to `projects/{project-name}/` with organized subfolders, not random locations
- **Produce dual-format outputs** — `.md` + `.docx` for documents, `.csv` for tables
- **Write session logs** tracking what was produced, inputs used, and outstanding gaps
- **Cite sources** by publication number, date its knowledge, and flag uncertainty
- **Use current interagency facts** (e.g., USAID dissolved 2025 → DoS/BHR is lead agency)
- **Stay UNCLASSIFIED** and put a "DRAFT — verify before acting" footer on everything
- **Understand the app architecture** enough to help with development or use

### Additional references

- [docs/compatibility/ai_assistant_guide.md](docs/compatibility/ai_assistant_guide.md) — Multi-AI orientation
- [docs/compatibility/external_ai_safe_use.md](docs/compatibility/external_ai_safe_use.md) — Safe usage patterns

### Claude Code skills

10 project-level skills in `.claude/skills/` provide operator shortcuts:

| Skill | Purpose |
|---|---|
| `echelon-context` | Detect and apply echelon modifiers |
| `doctrine-reference` | Look up USMC/joint publications by topic |
| `murder-board` | Adversarial design review (with doc anchoring) |
| `scenario-runner` | Run and compare agent responses |
| `agent-scaffolder` | Multi-file agent creation checklist |
| `automated-skill-builder` | Find and build new skills |
| `source-audit` | Audit source reference quality |
| `verifier-dashboard` | Evidence-capture for /verify |
| `run-server` | Standardized server startup |
| `agent-catalog` | Print live agent roster |

These are Claude Code-specific and have no effect on other AI tools.

## API reference

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for full endpoint examples.

Quick check that the server is running:

```bash
curl http://127.0.0.1:8000/health
# {"status": "ok", "classification": "UNCLASSIFIED", "human_review": "required"}
```

## What it does not do

- Does not call an LLM at runtime
- Does not ingest classified or CUI material
- Does not connect to email/calendar without explicit connector setup
- Does not make personnel, legal, medical, or command decisions
- Does not replace official guidance or formal staff processes

## Security and governance

- [SECURITY.md](SECURITY.md) — Vulnerability reporting
- [DISCLAIMER.md](DISCLAIMER.md) — Legal disclaimer
- [docs/data_governance.md](docs/data_governance.md) — Data handling policy
- [docs/core_documents/roadmap.md](docs/core_documents/roadmap.md) — Current roadmap

## License

[MIT](LICENSE)
