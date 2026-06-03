---
name: usmc-monitoring
description: Use when monitoring MARADMINs, Navy or DoD message feeds, reserve-readiness requirements, and other public-source updates that may affect drill, admin, PME, travel, or training obligations. Prefer existing message-watch, MARADMIN, reading, and custom-watch-feed routes before building a new watch workflow.
---

# USMC Monitoring

## Purpose

Keep reserve obligations and policy changes visible without requiring constant manual checking.

## When To Use

- MARADMIN and message-watch reviews.
- Reserve admin and readiness checks.
- PME, travel, GTCC, medical, or training change monitoring.
- Public-source update scans before building a brief.

## When Not To Use

- When official interpretation or legal determination is required.
- When the needed source is not public and no approved local summary is available.

## Preferred Repo Paths

Use existing repo surfaces first:

- `GET /maradmins/feed`
- `POST /maradmins/refresh`
- `GET /message-watch/navadmins`
- `POST /message-watch/navadmins/refresh`
- `GET /message-watch/alnavs`
- `POST /message-watch/alnavs/refresh`
- `GET /message-watch/dod/feed`
- `POST /message-watch/dod/refresh`
- `GET /reading-list/sources`
- `GET /custom-watch-feeds`
- `POST /custom-watch-feeds/{feed_id}/refresh`

## Monitoring Focus

- Reservist obligations and readiness.
- PME, distance education, and funded seminar opportunities.
- Fitness, medical, dental, admin, GTCC, travel, and training requirements.
- Awards, promotion, boards, MOS, manpower, or mobilization topics.
- GENAI, data, cyber, analytics, and modernization opportunities.

## Workflow

1. Pull the relevant public-source watch feeds or summaries.
2. Ignore noise and summarize only meaningful changes.
3. Highlight action items, dates, eligibility, and affected populations.
4. Separate confirmed source language from inference.
5. Compare new changes against current action items, handoffs, or briefs when available.
6. Recommend follow-up checks when a source appears stale, partial, or ambiguous.

## Output Format

- Source summary.
- What changed.
- Why it matters.
- Affected population.
- Dates and deadlines.
- Recommended follow-up.
- Source links or identifiers.

## Safety And Review Rules

- Do not claim official interpretation when source language is ambiguous.
- Link or cite the original source whenever possible.
- Keep output UNCLASSIFIED and public-source grounded.
- Do not store credentials, CAC details, or unnecessary PII.

## Failure Modes

- Treating routine traffic as meaningful change.
- Missing eligibility nuances.
- Summarizing stale cached data as if it were current.
- Drifting from source text into unsupported policy interpretation.

## Verification Checklist

- Source freshness checked.
- Key dates captured.
- Affected population named or marked unclear.
- Recommendation strength matches the source evidence.
