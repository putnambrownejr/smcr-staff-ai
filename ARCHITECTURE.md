# Architecture

A honest map of what this system is, what it does, what is a real working layer,
and what is scaffolding for future work.

---

## What This Is

A local-first advisory toolkit for SMCR staff workflows. It runs on your machine.
No cloud infrastructure, no LLM calls at runtime — the reasoning comes from your
connected AI assistant reading the repo patterns, or from a human reading structured
output. Advisory drafts only; human review required before acting on anything.

---

## The Real Spine (three things that actually work)

### 1. Advisory Agent Layer

`app/services/agents/` — ~35 active agents, each implementing the `Agent` base class.

Pattern: `AgentContext` in → structured text advisory out. Each agent wraps a domain
(staff echelon, MOS, function) with citations, confidence level, and human-review
warnings. The registry (`registry.py`) exposes them all via `POST /agents/{id}/run`.

**Where to look first:** `app/services/agents/base.py`, `app/services/agents/registry.py`,
any `*_agent.py` file — they all follow the same pattern.

### 2. JSON File-Store Continuity

All live user state (handoffs, actions, travel cases, battle rhythm, section memory,
opportunities, drill plans, MARADMIN feeds) is persisted as JSON files under the
local-context storage home (default: `%LOCALAPPDATA%\smcr-staff-ai` or
`$SMCR_STAFF_AI_HOME` if set).

This is the "survives between drills" value. It actually works.

**Key services:** `app/services/session/handoff_store.py`,
`app/services/actions/tracker.py`, `app/services/staff/battle_rhythm_store.py`,
`app/services/connectors/travel_case_store.py`.

### 3. Dashboard

`app/static/dashboard/` — a single-page browser app (HTML + vanilla JS + CSS).
Served at `http://localhost:8000/dashboard`. Aggregates the advisory agent layer
and the file-store continuity layer into an operator interface.

Lane navigation: Overview / Watch / Bench+Files / Workflows / Workspace.

---

## Stub / Scaffolding Layers (real interfaces, no semantic implementation)

### RAG Layer — interface stubs, not a retrieval foundation

`app/services/rag/` defines chunking, embeddings, pipeline, retriever, and vector store.
In practice:
- `LocalHashEmbeddingProvider` returns the first 16 bytes of a SHA-256 digest — deterministic
  noise, not a semantic embedding.
- `LocalVectorStore.search()` ignores its own vectors and ranks by lexical term intersection.
  It is keyword overlap wearing a vector-store interface.

This establishes the *interface shape* for a future real RAG implementation. Any actual
semantic retrieval work replaces both files wholesale behind the existing interface.
Do not attempt to incrementally improve the hash embedder.

### SQLite Database — vestigial, not used at runtime

`app/db/models.py` defines five SQLModel tables: `Document`, `DocumentChunk`,
`MessageRecord`, `CalendarPlan`, `OrgUnit`. The `init_db()` step creates them.

At runtime, **no route or service reads or writes these tables**. All live persistence
is through the JSON file stores above. The tables represent a future doctrine-corpus
ingestion schema that has not been wired yet.

If you are evaluating this codebase: the SQLite file is created by setup but unused
by the running application. This is a deliberate "future schema" decision, not a bug.

---

## Route Surface

39+ FastAPI routes across:

| Prefix | Purpose |
|---|---|
| `/agents` | Run any advisory agent by ID |
| `/planning` | Staff-package and planning-cell workflows |
| `/staff` | Staff council, section planners, admin workflows |
| `/training` | Training scenarios, S3/S4 planning, TDG |
| `/actions` | POAM / action item tracking |
| `/chief` | Chief/Aide brief and orchestrator |
| `/career` | FitRep, PME, opportunity watch |
| `/dashboard` | Dashboard data aggregation |
| `/maradmins` | MARADMIN feed ingest and refresh |
| `/billets` | SMCR billet recommendations |
| `/org` | Unit hierarchy and exercise cadence |
| `/demo/*` | Stateless demo versions of major routes |

Full inventory: `http://localhost:8000/docs`

---

## Key Files for Orientation

| File | What it tells you |
|---|---|
| `app/main.py` | All routers registered; app factory |
| `app/services/agents/registry.py` | Every agent, its ID, and description |
| `app/services/agents/base.py` | The `Agent` base class all agents extend |
| `app/services/agents/source_refs.py` | Citation and trust-marker patterns shared by all agents |
| `app/core/config.py` | All configurable paths and settings |
| `app/core/security.py` | PII detection, sensitive-content detection, redaction |
| `docs/core_documents/workflow_map.md` | How routes combine into real operating flows |
| `docs/core_documents/CONTRIBUTING_QUICKSTART.md` | First-run through first commit |
| `skills/README.md` | Operator-facing skill catalog |
| `data/seed/` | Example data shapes for every major entity |
| `docs/handoffs/README.md` | Cross-account handoff relay + current open threads |

---

## What Is Not Here

- **No LLM calls at runtime.** Advisory text is templated and structured. Connect your
  own AI assistant (Claude, ChatGPT, etc.) to the repo for generative reasoning.
- **No auth server.** `LocalApiKeyDependency` gates personal routes behind a locally
  configured passphrase — not OAuth, not JWT.
- **No live email or calendar connectors.** Interface stubs exist; live providers are
  not implemented. The `connector-adapter` skill handles normalization of externally
  collected data.
- **No deployed backend.** Local only. `uvicorn app.main:app --reload` from the repo root.

---

## Storage Pattern Detail

Every persisted domain uses the same scheme: `SHA256(user_key)[:24] → {digest}.json`
under a dedicated subdirectory of `local_context/`. Each store is a standalone class
that reads and writes one JSON blob per user key.

`database_url` and `vector_store_backend` exist in `Settings` as reserved fields for
future use — they are not wired to any code today. The SQLite file is created by setup
but unused by the running application.

---

## Multi-User Extension Point

`user_key` is the isolation boundary for all stores. To support shared workspaces without
a full database migration:

- Introduce a `group_key` alongside `user_key` in stores that should be shared.
- Personal-only stores (`section_memory`, `bench_sections`, `handoffs`) reject group keys.
- Collaborative stores (`battle_rhythm`, `drill_plans`) accept either.
- The SHA256 path scheme works for both; group keys need a distinct namespace (e.g. `grp_{key}`).
- Concurrent write safety would require file locking or a move to SQLite at that point.

Do not add `group_key` until a concrete shared-workspace use case exists.

---

## Safety Posture

UNCLASSIFIED-only. Agents include allowed-source lists, disallowed inputs, and
human-review flags. `app/core/security.py` detects likely sensitive inputs and forces
generic training/checklist-style responses. All outputs are advisory drafts requiring
human review before any action is taken.
