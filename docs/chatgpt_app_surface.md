# ChatGPT App Surface

This is an **optional/quarantined surface**, not the primary product path.

This file defines the recommended first-pass ChatGPT-facing surface for `smcr-staff-ai`.

## Intended Archetype

Initial archetype: `tool-only`

Why:

- the repo already has a strong backend-first contract
- the highest-value workflows are API-first and largely textual
- private/local context should stay out of the first ChatGPT-facing surface
- stateless demo tools are already available and safer to expose first

This follows the current OpenAI Apps SDK direction: define a small set of clear tools first, then add richer UI or private data integration later.

## First-Pass Tool Set

These are the recommended first tools to expose through a ChatGPT app or MCP tool layer:

1. `chief_brief_demo`
   - route: `GET /demo/chief/brief`
   - use when: the user wants a concise triage brief

2. `career_watch_demo`
   - route: `GET /demo/career/watch`
   - use when: the user wants PME, FitRep, opportunity, or self-development awareness

3. `summarize_text_demo`
   - route: `POST /demo/analysis/summarize`
   - use when: the user pastes notes or text and wants structure

4. `draft_staff_product_demo`
   - route: `POST /demo/staff-products/draft`
   - use when: the user needs an OPORD/WARNO/FRAGO/SITREP/AAR/correspondence scaffold

5. `run_staff_agent_demo`
   - route: `POST /demo/agents/{agent_id}/run`
   - use when: the user wants targeted help from a specific staff or MOS agent

## Why These Tools First

- all are stateless or stateless enough for demo use
- all are already documented in FastAPI/OpenAPI
- none require local user documents, handoffs, or private uploads
- they are useful enough to demonstrate the app’s value immediately

## What Should Wait

These should not be first-pass public ChatGPT tools:

- local context upload and document reads
- live personal handoff mutation without explicit confirmation
- personal opportunity tracking
- future email/calendar connectors
- any workflow that depends on local machine state or private records

Those can come later as authenticated/private tools once the runtime and trust model are nailed down.

## Suggested MCP / Apps Mapping

Recommended tool descriptions should start with “Use this when...” and stay behavior-based:

- `chief_brief_demo`: Use this when the user wants a concise drill/admin/career triage brief.
- `career_watch_demo`: Use this when the user wants a self-development and readiness watch list.
- `summarize_text_demo`: Use this when the user pastes notes or working text and needs summary, due-outs, and follow-up questions.
- `draft_staff_product_demo`: Use this when the user needs an advisory military staff-product scaffold.
- `run_staff_agent_demo`: Use this when the user wants targeted help from a specific advisory staff agent.

## Recommended Next Step

If we continue toward a real ChatGPT app, the next implementation step should be:

1. preserve this stateless surface as the public contract
2. add app/tool metadata and hosting guidance
3. test in ChatGPT developer mode with a remote or tunneled runtime
4. only then consider authenticated/private tools
