# AGENTS.md

This file tells humans and connected AI tools how to orient inside `smcr-staff-ai`.

## Project Purpose

`smcr-staff-ai` exists to help Marine Corps Reservists stay aware, stay sharp, and stay ahead of the friction of reserve service by turning scattered obligations, staff problems, and training demands into organized, advisory, usable outputs.

The project has three core pillars:

1. **Awareness**
   - drill rhythm
   - admin suspense
   - source updates
   - chief brief / readiness watch
   - personal document continuity

2. **Readiness and edge**
   - staff planning
   - training design
   - FRAGO to CONOP flow
   - AAR / SITREP / correspondence products
   - case studies, TDGs, current-event-driven scenarios

3. **Friction reduction**
   - drill prep
   - AT prep
   - DTS / GTCC / admin reminders
   - PKI / CAC support
   - installation / base practical issues
   - continuity between drills

All outputs are advisory and require human review. The repo is not a source of command authority.

## Required Repo Search Behavior For AI

If you are an AI connected to this repository, do **not** answer from vague memory alone when the user asks what the repo can do or which tool to use.

Before answering non-trivial questions, search the repo for the relevant:

- agents
- app tools
- API routes
- schemas
- docs
- example payloads

At minimum, check these places first:

1. `README.md`
2. `docs/core_documents/project_purpose.md`
3. `docs/compatibility/ai_assistant_guide.md`
4. `app/api/routes/`
5. `app/services/agents/registry.py`
6. `docs/examples/`

Recommended search patterns:

```powershell
rg -n "build_staff_package|frago|conop|aar|agent|route|tool" <repo-root>
rg -n "class .*Agent|def build_.*agent|citation_required" <repo-root>\app\services\agents
rg -n "@router|APIRouter|response_model" <repo-root>\app\api\routes
```

## How To Choose Capability

When helping a user, prefer this order:

1. existing repo agents and workflows
2. existing routes and schemas
3. new code only if the capability is genuinely missing

Do not recommend rebuilding connector auth, generic calendar/email tooling, or other commodity capabilities when the repo already intends to reuse them.

## Scope Discipline

If a proposed feature does not clearly improve one of these:

- awareness
- readiness / edge
- friction reduction

then treat it as lower priority, even if it sounds interesting.

## Safety

Keep everything UNCLASSIFIED.

Do not add:

- classified information
- CUI
- COMSEC
- keying material
- real frequencies
- call signs
- precise movements
- unnecessary PII
- sensitive operational details

Treat local notes and uploads as advisory context, not authoritative truth.
