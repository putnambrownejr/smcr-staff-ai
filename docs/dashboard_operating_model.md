# Dashboard Operating Model

This dashboard is meant to act like a working staff board, not a generic admin homepage.

The strongest patterns behind it come from:

- `Build Web Apps: frontend-testing-debugging`
- `Build Web Apps: frontend-app-builder`
- `daily-ops-brief`
- `analyst-brief`
- `business-analyst`
- `project-manager`

## Purpose

The dashboard should answer three questions quickly:

1. What matters now?
2. How healthy is the underlying picture?
3. What should the user do next?

## Core Lenses

### 1. Daily Brief Lens

This lens is action-oriented and should feel like a reserve-aware Chief/Aide triage board.

Primary sections:

- executive snapshot
- must-do
- should-do
- can-defer
- waiting-on
- blockers
- top leverage actions
- prep and follow-up

Primary inspiration:

- `daily-ops-brief`

Mapping to current repo data:

- `chief_brief.action_items`
- `chief_brief.top_priority_items`
- `chief_brief.drill_plans`
- `admin_readiness.items`
- `career_watch.watch_items`
- `documentation_updates`
- `document_summary`

Behavioral standard:

- hard commitments and urgent due-outs rise to must-do
- medium-priority work becomes should-do
- low-priority watch items become can-defer
- missing docs, stale handoff, and unreviewed source updates become blockers or waiting-on cues

### 2. Analyst Brief Lens

This lens is evidence-oriented and should feel like a compact staff analyst or data-health review.

Primary sections:

- executive summary
- data quality notes
- KPI summary
- anomalies
- likely causes
- assumptions
- follow-up checks

Primary inspiration:

- `analyst-brief`

Mapping to current repo data:

- `document_summary`
- `career_watch`
- `admin_readiness`
- `documentation_updates`
- `tracked_opportunities`
- stale-handoff detection

Behavioral standard:

- start with data quality before conclusions
- call out missing or stale local context
- avoid pretending local uploads are authoritative
- highlight unresolved source freshness questions
- recommend concrete verification steps

## Supporting Sections

### Priority Queue

Purpose:

- preserve a direct task-first list from the Chief/Aide workflow

Use when:

- the user needs immediate action ordering

### Local Document Watch

Purpose:

- show support-document coverage, review due items, expirations, and media/local-context breadth

Use when:

- the user needs to know whether their local context is sufficient

### Opportunity Watch

Purpose:

- keep ADOS and SMCR BIC opportunities visible without burying them inside broader career cards

Use when:

- the user is actively managing billets, broadening assignments, or timing-sensitive openings

### Source Updates

Purpose:

- keep doctrine/admin freshness visible

Use when:

- users are relying on summaries or templates that might be stale

## Skill And Agent Mapping

### `daily-ops-brief`

Best use:

- drive the Daily Brief card model and prioritization language

Should influence:

- must-do / should-do / can-defer structure
- top leverage actions
- prep follow-up framing

### `analyst-brief`

Best use:

- drive the Analyst Brief logic and future data-merge summaries

Should influence:

- data quality first ordering
- anomaly presentation
- reproducible follow-up checks

### `business-analyst`

Best use:

- convert new dashboard ideas into explicit scope, acceptance criteria, and non-goals

Should influence:

- future dashboard feature planning
- use-case onboarding
- workflow boundary decisions

### `project-manager`

Best use:

- POAM and milestone-style planning once action tracking becomes first-class

Should influence:

- future dashboard roadmap cards
- dependency and suspense tracking
- action-owner clarity

### `Build Web Apps: frontend-testing-debugging`

Best use:

- every meaningful dashboard UI change

Should influence:

- runtime verification
- responsive checks
- regression discipline

### `Build Web Apps: frontend-app-builder`

Best use:

- deliberate redesign or dashboard v2, not every feature tweak

Should influence:

- future visual overhaul
- component system discipline
- concept-to-implementation fidelity

## Recommended Next Dashboard Expansions

### 1. POAM / Action Tracking

Add:

- owner
- suspense
- status
- linked document or source
- drill / admin / career category

This is the natural next evolution of the Daily Brief lens.

### 2. Multi-Source Merge Workbench

Add:

- merge multiple uploads
- deduplicate due-outs
- reconcile names/dates
- produce an analyst brief from combined sources

This is the natural next evolution of the Analyst Brief lens.

### 3. Pinned Workflows

Add:

- one-click cards for:
  - drill prep
  - FitRep prep
  - DTS voucher
  - TDG generator
  - correspondence draft
  - POAM draft

This makes the dashboard feel less like a report and more like a staff workbench.

### 4. Use-Case Catalog

Add:

- tie training media and future transcripts to dashboard launches
- map each use case to routes, agents, and current implementation status

## Guardrails

- local uploads remain advisory and non-canonical
- source-update candidates are warnings until reviewed
- opportunities do not determine eligibility or approval
- the dashboard should reduce confusion, not create false certainty
- visual polish should never outrun semantic clarity
