---
name: personal-chief-of-staff
description: Use when a reservist needs a full-picture daily or drill-period operating brief that pulls together handoffs, action tracker status, career watch, PME gaps, FitRep suspense, DTS/GTCC due-outs, career opportunities, and drill prep state in one pass. More comprehensive than chief-brief-ops — use this when the user wants everything on the table, not just commitments and blockers. Triggers on phrases like "what do I need to do," "give me my full picture," "where am I on everything," "prep me for drill," "catch me up," or any request to combine career, admin, and readiness state into one operating view.
---

# Personal Chief of Staff

## Purpose

Surface the complete reserve-officer operating picture in one pass: readiness posture, open actions, career gaps, admin due-outs, and drill prep state. Where `chief-brief-ops` handles the daily triage brief, this skill handles the fuller situation report — the kind you'd build before a drill weekend, a board, or a long gap between sessions.

## When To Use

- Before a drill weekend — pull everything that needs attention before first formation.
- After a gap — returning from leave, travel, or a long break between sessions.
- Career checkpoint — PME window coming up, FitRep occasion approaching, board season.
- "What do I need to do" moments — the user wants the full list, not a filtered slice.
- When `chief-brief-ops` feels too narrow for what the user is actually asking.

## When Not To Use

- When the user only wants a focused daily brief or a single-topic summary (use `chief-brief-ops` instead).
- When no local workspace is loaded and demo data is the only source — flag this and offer the demo brief instead.
- When an official personnel or admin product is required rather than an advisory summary.

## Preferred Repo Paths

Pull all available local context before synthesizing:

**Core picture:**
- `GET /chief/brief/{user_key}` — primary orchestration brief with handoff, documents, drill plans, opportunities
- `GET /career/watch/{user_key}` — PME gaps, FitRep reminders, career trends, recommended courses, opportunities
- `GET /admin/readiness/{user_key}` — FitRep reminders, admin watch items, DTS/GTCC gaps, missing docs
- `GET /actions?user_key={user_key}` — open tracked action items with owner, suspense, and status

**Drill prep:**
- `GET /calendar/drill-prep-plan` (or latest stored plan) — pre-drill tasks and ICS state
- `GET /handoffs/{user_key}` — session handoff: PME, FitRep occasions, admin items, recurring checks

**Opportunities:**
- `GET /opportunities?user_key={user_key}` — tracked ADOS and SMCR BIC opportunities

**Demo fallback (no personal workspace):**
- `GET /demo/chief/brief`
- `GET /demo/career/watch`

## Workflow

1. Check whether a personal workspace is loaded. If not, warn and offer the demo brief.
2. Pull the chief brief, career watch, and admin readiness in parallel — these three together form the full picture.
3. Pull the open action tracker — separate the high-priority and overdue items from the queue.
4. Pull the handoff to surface recurring checks and PME/FitRep dates not already in the brief.
5. Pull tracked opportunities and surface any with approaching deadlines.
6. Synthesize across all sources — de-duplicate, merge overlapping items, and prioritize by suspense and consequence.
7. Produce the full brief. Clearly separate the triage stack (act now), the background queue (act soon), and the watch list (no action yet but don't lose sight of it).
8. Offer to promote due-outs into tracked actions if the user wants continuity.

## Output Format

- **Readiness posture** — one line: green / watch / degraded, anchored to the next drill date.
- **Act now** — critical due-outs, overdue items, and hard suspense approaching within the week.
- **Act soon** — PME windows, FitRep prep, DTS/GTCC follow-through, and career actions due in the next 30 days.
- **Career picture** — PME gaps, board season awareness, tracked opportunities with deadlines.
- **Admin picture** — missing documents, stale references, GTCC/travel due-outs.
- **Drill prep state** — pre-drill tasks remaining, ICS export status if relevant.
- **Watch list** — items with no immediate action but real consequence if they drift.
- **Stale or missing inputs** — call out what couldn't be pulled and why.

## Safety And Review Rules

- Treat all outputs as advisory drafts — none are authoritative personnel or admin decisions.
- Do not invent handoff data, FitRep dates, or suspense items not present in the stored context.
- Flag stale handoffs explicitly rather than presenting old data as current.
- Do not claim live calendar or email reads unless connector-fed inputs were actually provided.
- Keep all output UNCLASSIFIED.

## Failure Modes

- Handoff is stale — dates and watch items may not reflect the current drill period.
- Action tracker is empty — the user has been tracking things elsewhere and the local tracker is cold.
- Career watch has no PME data — handoff was never populated with PME program details.
- Drill prep plan doesn't exist yet — offer to generate one from the next stored drill date.
- Missing local documents (RQS, BIO, orders) flagged but not available — surface the gap clearly.

## Verification Checklist

- Readiness posture line anchored to the next confirmed drill date.
- Act-now stack contains only items with real suspense or consequence — not filler.
- PME gaps and FitRep occasions are surfaced if present in the handoff or career watch.
- Stale or missing inputs are called out explicitly, not silently dropped.
- Tracked opportunities with approaching deadlines appear in the career picture.
- Output is de-duplicated across the chief brief, career watch, and admin readiness sources.
