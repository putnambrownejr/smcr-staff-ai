---
name: source-trust-review
description: Use when reviewing the freshness, verification status, and trust level of doctrine, admin, or public-source material. Routes follow-up work based on trust state — verified-current, needs-review, or update-detected. No external analog for this domain-specific trust-propagation pattern.
---

# Source Trust Review

## Purpose

Keep the source layer honest. Surface what is verified-current, what needs a human review pass,
and what has a pending update signal — so advisory outputs are grounded in reliable material
and operators know when to pause before acting on a source.

## When To Use

- Before building a staff product that cites doctrine or policy (OPORD, CASEVAC plan, ORM worksheet)
- After a MARADMIN scan surfaces a potential change to tracked source material
- When a source reference feels stale but you don't know its actual status
- When conducting a periodic source freshness audit before a drill

## Trust States

| State | Meaning | Action |
|---|---|---|
| `verified-current` | Source confirmed fresh, no pending updates | Use freely, cite confidently |
| `needs-review` | Source not checked recently or flagged as potentially outdated | Human review before citing; note "verify before use" |
| `update-detected` | Monitoring system flagged a potential change | Do not use until reviewed; route to source update workflow |
| `placeholder` | Source noted but never fetched or ingested | Do not cite; flag as gap |

## Preferred Repo Paths

Use existing repo surfaces:

- `GET /source-updates` — list pending documentation update candidates
- `POST /source-updates/{id}/review` — mark a candidate as reviewed, confirmed, or ignored
- `GET /maradmins/feed` — check recent MARADMINs that may affect tracked sources
- `POST /maradmins/refresh` — pull latest feed before a trust review
- `GET /reading-list/sources` — check reading list source freshness

## Workflow

1. Identify the sources cited in or relevant to the current task
2. For each source, determine its trust state using the table above
3. Flag any `update-detected` or `needs-review` sources explicitly in the output
4. For `update-detected`: route to `POST /source-updates/{id}/review` before proceeding
5. For `needs-review`: note the gap in the output and recommend the human verify before using
6. For `placeholder`: note that the source exists in the manifest but has not been ingested

## Output Format

- Source name and type
- Current trust state
- Last verified date (if known)
- Recommended action
- Routing path for follow-up

## Safety Rules

- Never silently drop a needs-review or update-detected source from an output
- Never upgrade a source's trust state without a human confirmation step
- Flag uncertainty explicitly — "source status unknown" is an acceptable output
- Do not infer current policy from stale source material

## Failure Modes

- Treating a cached doc as authoritative when an update has been detected
- Missing a MARADMIN that supersedes a cited policy
- Citing a placeholder source that was never actually ingested
- Silently degrading output quality when sources are stale instead of flagging it
