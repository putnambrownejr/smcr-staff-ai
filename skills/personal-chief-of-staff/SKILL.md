---
name: personal-chief-of-staff
description: Use when you need a single integrated operator brief covering handoff state, open actions, career watch, travel and admin due-outs, and drill prep in one pass. Extends chief-brief-ops by unifying the full personal admin and continuity surface, not just the chief brief output.
---

# Personal Chief of Staff

## Purpose

One workflow to answer: "What is the full picture of my reserve obligations, open items,
and continuity state right now — and what do I need to do next?"

This skill unifies the surfaces that chief-brief-ops surfaces separately:
handoff continuity + action tracking + career watch + admin due-outs + drill prep.

## When To Use

- Morning before a drill weekend — full situational awareness in one pass
- After a gap (returning from leave, picking up after two weeks)
- Before a command-group sync where you need the complete picture, not just the brief
- When `handoff_is_stale` is flagged — need a full refresh across all surfaces

## When Not To Use

- When you only need the chief brief — use `chief-brief-ops` instead
- When you only need to monitor sources — use `usmc-monitoring` instead
- When you only need to convert meeting notes — use `meeting-to-action` instead

## Preferred Repo Paths

Run in this order for a full picture:

```
1. GET /chief/brief/{user_key}
   → handoff state, action items, next-drill readiness, battle rhythm health,
     handoff_is_stale flag

2. GET /career/watch/{user_key}
   → FitRep watch, PME watch, tracked opportunities, career gaps

3. GET /actions?user_key={key}
   → open POAMs, blocked items, waiting-on, suspense dates

4. GET /admin/readiness/{user_key}
   → travel case status, document gaps, GTCC/DTS due-outs, admin friction

5. GET /dashboard/data/{user_key}
   → unified view if preferred over individual calls
```

Demo path (no auth, sample data):
```
GET /demo/chief/brief
GET /demo/career/watch
```

## Workflow

1. Pull the full picture across all five surfaces above
2. Triage: sort everything into must-do, should-do, can-defer, waiting-on
3. Flag stale handoff, expired documents, or missed suspenses explicitly
4. Identify the single most important action before the next drill
5. Surface any admin friction (DTS, MROWS, RIDT) that needs action
6. Recommend follow-up routes if deeper work is needed in any lane

## Output Format

- **Handoff status** — fresh / stale / missing, with age if known
- **Must-do before next drill** — max 5, ranked
- **Open actions** — owner, suspense, status for each
- **Career watch** — FitRep due, PME gap, tracked opportunities
- **Admin due-outs** — DTS, MROWS, RIDT, document expirations
- **Recommended next single action** — the one thing that matters most

## Safety Rules

- Do not claim live mailbox or calendar reads unless connector-fed inputs were provided
- Flag stale or missing inputs explicitly — do not fill gaps with assumptions
- Keep all output UNCLASSIFIED and advisory
- Admin claim details (DTS denial codes, MROWS citations) are advisory; verify with Admin

## Failure Modes

- Stale handoff treated as current state
- Missed FitRep or PME suspense outside the stored context window
- Admin due-outs buried under lower-priority items
- Assuming travel is covered when DTS/MROWS status is unknown
