---
name: murder-board
description: Relentless one-question-at-a-time design review before implementation. Walks every branch of the decision tree, auto-explores the codebase to skip questions the code already answers, and enforces this project's security and architecture constraints.
---

# Murder Board — smcr-staff-ai Design Review

## Purpose

Force a thorough design conversation before touching implementation. Ask one focused question at a time, follow every branch, resolve inter-dependencies, and skip questions the codebase already answers.

## When to Use

- Before implementing any new agent, dashboard feature, API route, or data model change
- When requirements arrive informally and edge cases haven't been discussed
- When a change touches more than one layer (agents + API + dashboard + tests)
- When two or more valid approaches exist and tradeoffs haven't been weighed
- Before any architectural change (new storage pattern, new service, schema change)

## When Not to Use

- Trivial changes: typo fixes, single-line patches, copy edits
- When `murder-board-docs` is better (the area has recorded decisions in CLAUDE.md or PRODUCT.md)
- When the design was already murder-boarded and this is pure execution
- Hotfixes where the correct fix is unambiguous

## Workflow

Strict interview mode. One question per turn. Never present a list.

### Steps

1. **Scope the design surface.** Auto-explore: read relevant files under `app/`, `tests/`, `CLAUDE.md`, `.claude/skills/`. Record what the code already answers.

2. **Identify the root decision.** Ask the single most load-bearing design choice first.

3. **Branch on the answer.** Each answer closes some branches, opens others. Follow open branches depth-first.

4. **Resolve inter-dependencies.** When two decisions constrain each other, state what's locked so far, explain the constraint, then ask.

5. **Keep asking until the tree is exhausted.** Do not summarize or propose implementation until every branch is resolved or explicitly deferred.

6. **Produce a design summary.** Numbered decision log: each decision, chosen option, stated reason.

7. **Hand off to implementation.** Only after the summary is accepted.

## Project-Specific Constraints to Enforce

During the grill, actively challenge designs that violate these:

- **UNCLASSIFIED only.** Any design that would store, process, or display classified info, CUI, COMSEC, real frequencies, call signs, or precise unit movements must be rejected.
- **No LLM at runtime.** The server does not call any AI API. Advisory text comes from static lookups and templates. If the design assumes runtime AI, challenge it.
- **Flat JSON storage.** All user state is flat JSON under `%LOCALAPPDATA%\smcr-staff-ai\`. No database. Designs requiring relational queries or migrations need justification.
- **Vanilla JS SPA.** No frontend framework. No bundler. If the design assumes React/Vue/build tooling, challenge it.
- **FastAPI backend.** Routes in `app/api/routes/`, schemas in `app/schemas/`, services in `app/services/`.
- **Human review required.** All agent outputs are advisory drafts. Designs that auto-execute agent recommendations without human confirmation must be challenged.
- **35-agent registry.** New agents must justify why an existing agent can't be extended. Prefer updating an existing agent over adding a new one.

## Rules

- **One question per turn.** Never bundle multiple questions.
- **No leading questions.** Present options neutrally.
- **State what code already tells you.** Cite file and lines.
- **Defer is valid.** Record deferred decisions, don't re-ask.
- **No code mid-board.** No writing, scaffolding, or stubbing until the design summary is accepted.
- **Record the full decision log.** Suitable for pasting into a commit message or PR description.
