# AI Assistant Guide

How any connected AI tool should read and use this repository.
Applies to Claude, ChatGPT, Gemini, Copilot, Grok, and any other assistant with repo access.

---

## Start Here

Before answering non-trivial capability or workflow questions, search the repo. Do not rely on generic memory.

Priority search targets:

1. `README.md` — project overview and feature index
2. `docs/agents_setup/AGENTS.md` — agent catalog and intended uses
3. `docs/core_documents/project_purpose.md` — mission fit and scope
4. `docs/architecture.md` — service layout and key design decisions
5. `app/services/agents/registry.py` — authoritative list of all agents
6. `app/api/routes/` — all available endpoints
7. `docs/examples/` — canonical example payloads

Useful search patterns:
```
rg -n "build_staff_package|frago|conop|aar|agent|tool|route" app/
rg -n "class .*Agent|def build_.*agent" app/services/agents/
rg -n "@router|APIRouter" app/api/routes/
```

---

## What This Repo Is

An UNCLASSIFIED public-source advisory toolkit for SMCR (Selected Marine Corps Reserve) staff workflows.
It runs locally. All sensitive user context stays on the user's machine.

The repo provides:
- FastAPI backend routes covering staff planning, admin, training, career, and org awareness
- Advisory agents covering staff echelons from company to division/group
- A local dashboard at `http://localhost:8000/dashboard`
- Demo routes (`/demo/*`) that work without any local state

---

## What Is and Is Not Available From GitHub Alone

**Available from GitHub:**
- Full API contract via FastAPI routes and Pydantic schemas
- All agent definitions and their advisory content
- Architectural reasoning through the modular service layout
- Demo workflows via `/demo/*` routes (no setup required)
- Seed manifests and example payloads in `docs/examples/`

**Not available from GitHub:**
- User-scoped local context (handoffs, uploaded documents, drill plans)
- Stored opportunities, tracked actions, or personal notes
- Email or calendar connector data
- Runtime secrets, environment variables, or local API keys

---

## How to Use This Repo as an AI Assistant

### If you only have the repo (no local runtime)
1. Read `README.md` and `docs/agents_setup/AGENTS.md` first
2. Use `/demo/*` routes as the reference for what the system produces
3. Help the user shape a request payload from `docs/examples/`
4. Refer the user to `http://127.0.0.1:8000/docs` to execute it locally

### If the user also has the local API running
The best front door is:
- `POST /planning/staff-package` — turns one problem into a full staff output

Recommended workflow:
1. Help the user shape the problem (unit, event, goal, constraints)
2. Build a valid JSON payload matching the schema
3. User executes at `http://127.0.0.1:8000/docs`
4. Refine the output — tighten the plan, sharpen decisions, draft follow-on products

Example starter prompt a user can give you:
```
Use my smcr-staff-ai repo as context. Before answering, search the repo
for the relevant agents, routes, schemas, and examples. Help me build
a valid JSON request for /planning/staff-package.
```

---

## Safe Sharing Rule

Do not encourage users to paste raw local context into hosted AI tools.
If a user wants to share local data with an external model, use:

- `POST /sharing/external-ai-packet`

This route strips raw local references, withholds identifying fields, and produces a scrubbed packet.
See `docs/compatibility/external_ai_safe_use.md` for safe sharing principles and provider-specific prompts.

---

## Mission Fit

Every output is UNCLASSIFIED and advisory. Human review is required before acting on any output.
Prioritize features that improve:
1. Awareness — what's happening, what's due, what changed
2. Readiness / edge — sharper products, better-prepared Marines
3. Friction reduction — less time on admin, more time on mission
