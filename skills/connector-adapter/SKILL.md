---
name: connector-adapter
description: Use when normalizing external calendar, email, or travel summaries into repo-native schemas and workflows. Bridges the gap between what external tools produce and what smcr-staff-ai routes consume — without pretending the repo owns OAuth or live connector state.
---

# Connector Adapter

## Purpose

Translate external inputs (calendar exports, email summaries, travel itineraries, RSS content)
into the repo-native schemas and workflow paths the rest of the system understands.

The repo is local-first and does not own OAuth. This skill is the boundary between
"something came from outside" and "the repo can act on it."

## When To Use

- You have a calendar export (.ics, JSON, or plain text) and want it as drill prep state
- You have an email summary and want to extract actions, due-outs, or handoff updates
- You have a travel itinerary and want to route it through the travel case workflow
- You have RSS/feed content that should become a source update or monitoring record
- Any time external data needs to enter the repo's local storage without manual re-entry

## What This Skill Does NOT Do

- It does not call external APIs directly
- It does not own OAuth tokens or credentials
- It does not scrape live services — it normalizes content you already have
- It does not bypass the UNCLASSIFIED posture

## Preferred Repo Paths

### Calendar / Drill Dates
```
POST /calendar/drill-details
  body: { text: "<ics export or plain-text schedule>",
          source_context_id, default_date }
  → extracts drill events, times, locations, due-outs
```

### Email → Actions
```
POST /analysis/summarize
  body: { text: "<email or thread summary>" }
  → structured summary with action items

POST /actions/track  (for each extracted action)
```

### Travel / Admin
```
POST /connectors/workflow-adapter
  body: { source_type: "travel_email", raw_content: "..." }
  → routes to travel case store and admin readiness

POST /travel-cases/{user_key}
  → stores normalized travel case record
```

### RSS / Source Feeds
```
POST /custom-watch-feeds/{feed_id}/refresh
  → pulls and stores latest items from a configured feed

POST /source-updates  (if content suggests a policy change)
  → creates a documentation update candidate for human review
```

## Normalization Rules

1. **Strip what the repo doesn't need** — remove OAuth tokens, raw credentials, full email threads, attachment binaries
2. **Preserve what matters** — dates, owners, suspense items, action verbs, source citations
3. **Flag uncertainty** — if the input is ambiguous, surface the ambiguity rather than guessing
4. **Route, don't store raw** — push through a repo route rather than storing raw external content in local context directly
5. **Respect UNCLASSIFIED** — if the input contains anything that looks classified, CUI, or OPSEC-sensitive, stop and flag it

## Output Format

- Source type identified (calendar / email / travel / feed)
- Normalized fields extracted
- Repo route recommended for each extracted item
- Ambiguities or gaps flagged explicitly
- Items that could not be normalized listed separately

## Failure Modes

- Treating an ambiguous date as confirmed
- Storing raw email content with PII instead of routing through the shared context store
- Missing an action item embedded in a thread
- Routing travel content to the wrong workflow (DTS vs. MROWS vs. RIDT)
