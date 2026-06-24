---
name: grill-with-docs
description: Design grilling session anchored to CLAUDE.md, PRODUCT.md, and the project's domain model. Challenges plans against documented decisions, sharpens terminology, and surfaces conflicts between proposed changes and existing architecture.
---

# Grill With Docs — smcr-staff-ai

Interview relentlessly about every aspect of a plan, anchoring each question to existing project documentation. Walk each branch of the decision tree, resolving dependencies one by one. For each question, provide a recommended answer.

Ask questions one at a time. Wait for feedback before continuing. If a question can be answered by exploring the codebase, explore instead of asking.

## Documentation to Anchor Against

During codebase exploration, read and cross-reference these sources:

| Document | What it governs |
|---|---|
| `CLAUDE.md` | Architecture facts, security constraints, key patterns, dev workflow |
| `PRODUCT.md` | Product vision, user personas, five-lane structure, what's in/out of scope |
| `app/services/agents/registry.py` | Agent registry — which agents exist and how they're organized |
| `app/services/staff/council.py` | Staff Council deliberation — how multi-agent routing works |
| `app/core/config.py` | Storage paths, settings, configuration |
| `app/api/routes/` | API surface — what endpoints exist |
| `app/static/dashboard/index.html` | Dashboard structure and UI patterns |
| `.claude/skills/` | Project-level skills |

## During the Session

### Challenge against existing architecture

When the user proposes something that conflicts with CLAUDE.md's architecture facts or security constraints, call it out immediately: "CLAUDE.md says the server has no LLM at runtime, but your proposal assumes an API call to Claude — which should change?"

### Challenge against the agent model

When the user proposes a new agent or capability, check whether an existing agent already covers that lane. "The fires-advisor already covers mortars and NSFS — would extending it be better than a new agent?"

### Sharpen domain language

When the user uses vague or overloaded terms, propose the project's canonical term:
- "staff section" vs "staff lane" vs "warfighting function" — which do you mean?
- "agent" vs "archetype" vs "advisor" — this project distinguishes between standalone agents and staff archetypes
- "echelon" has a specific meaning here (battalion / regiment / division_group)

### Discuss concrete scenarios

Stress-test domain relationships with specific scenarios. "If a battalion S-4 asks this question with echelon=battalion, and a division G-4 asks the same question with echelon=division_group, should the agent respond differently? How?"

### Cross-reference with code

When the user states how something works, verify against the code. "You said the Staff Council routes to all agents, but `council.py` only routes to the 16 staff archetypes — standalone agents like `ace` are excluded."

### Surface security constraint conflicts

Any design that would introduce classified info, PII beyond what's needed, external API calls at runtime, or weaken the human-review-required guarantee must be flagged explicitly.

## Rules

- **One question at a time.** Wait for the answer.
- **Anchor every challenge to a specific file.** Don't make abstract objections — cite the file and what it says.
- **No code mid-grill.** Don't write, scaffold, or stub until the design summary is accepted.
- **Deferred is valid.** Record it, move on, don't re-ask.
- **Produce a decision log.** Numbered list of decisions, chosen options, and reasons when the grill completes.
- **UNCLASSIFIED only.** Do not discuss or design features that would handle classified information.
