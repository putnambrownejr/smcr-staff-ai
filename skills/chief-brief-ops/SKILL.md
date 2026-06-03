---
name: chief-brief-ops
description: Use when turning commitments, blockers, local handoffs, action items, stored drill plans, and user context into a Chief of Staff / Aide style daily brief or drill-period operating picture. Prefer existing chief, career, action, and dashboard routes before inventing a new summary workflow.
---

# Chief Brief Ops

## Purpose

Turn available commitments, blockers, due-outs, local handoffs, and priorities into a clear operating brief.

## When To Use

- Morning planning.
- Drill-weekend prep.
- Midday reset.
- Before a command-group sync, XO sync, or update brief.

## When Not To Use

- When live calendar or mailbox access is required but only unstated assumptions are available.
- When an official command product is required instead of an advisory brief.

## Preferred Repo Paths

Use existing repo surfaces first:

- `GET /demo/chief/brief`
- `GET /demo/career/watch`
- `POST /connectors/chief-digest-plan`
- `POST /connectors/workflow-adapter`
- `POST /actions/from-chief-brief`
- `GET /dashboard`

Use private/local routes when the user wants stored context applied and an auth boundary is available:

- `POST /chief/brief`
- `GET /chief/brief/{user_key}`
- `GET /career/watch/{user_key}`
- `GET /actions`

## Workflow

1. Identify hard commitments, drill dates, and due-outs.
2. Pull or summarize current blockers and waiting-on items.
3. Separate must-do, should-do, can-defer, and follow-up checks.
4. Surface missing documents, stale handoffs, or admin friction when present.
5. Recommend the top three leverage actions.
6. Promote action items into the action tracker if the user wants continuity.

## Output Format

- Executive snapshot.
- Must-do.
- Should-do.
- Can-defer.
- Waiting-on.
- Blockers.
- Top three leverage actions.
- Prep work and follow-ups.

## Safety And Review Rules

- Draft summaries and action recommendations only.
- Do not claim live mailbox or calendar reads unless connector-fed inputs were actually provided.
- Keep all output UNCLASSIFIED and advisory.
- Flag stale or missing inputs instead of filling gaps with fiction.

## Failure Modes

- Stale handoff data.
- Hidden deadlines outside the provided context.
- Over-prioritizing easy admin tasks over real suspense risk.
- Missing owner or suspense fields on action items.

## Verification Checklist

- Hard commitments included.
- Top actions are realistic for the available time window.
- Waiting-on items have owners or next checks.
- Missing or stale inputs are called out explicitly.
