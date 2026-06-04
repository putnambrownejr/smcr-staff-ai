---
name: source-trust-review
description: Use when reviewing the trust state of doctrine, admin, or policy sources — checking which references are verified-current, which are flagged as needs-review or update-detected, and routing follow-up work cleanly. Triggers on phrases like "check my sources," "are my references current," "review doctrine freshness," "what needs to be verified," "update my source states," "check MARADMINs for changes," or any request to validate whether the references underlying a brief or product are still accurate.
---

# Source Trust Review

## Purpose

Walk through the repo's source-trust state in an organized pass: identify what is verified-current, what has been flagged as update-detected or needs-review, and turn the open items into concrete follow-up actions. The goal is to prevent advisory outputs from resting on stale or unverified references without the user realizing it.

## When To Use

- Before building a staff product, brief, or admin package that will be handed to a commander or routed formally.
- After a batch of MARADMINs comes through — check whether any affect doctrine or admin references you're relying on.
- At the start of a new drill period — verify that references used last drill are still current.
- When the dashboard source-watch ticker shows flagged items — move from awareness to action.
- Any time the user asks whether their references are current or wants to confirm freshness before use.

## When Not To Use

- When the user only wants a MARADMIN feed summary without acting on it (use `usmc-monitoring` instead).
- When official verification through proper channels is required — this skill produces advisory follow-up prompts, not authoritative source certification.
- When no source states or update candidates exist yet in the local workspace.

## Preferred Repo Paths

Pull the full source-trust picture before making any recommendations:

**Update candidates (detected but not reviewed):**
- `GET /documents/updates` — all flagged documentation update candidates
- `GET /documents/updates?status=new` — candidates not yet reviewed
- `GET /documents/updates?status=reviewed` — candidates reviewed but not yet accepted

**Verified source states:**
- `GET /documents/source-states` — all verified source state records

**Live feed checks:**
- `GET /maradmins/feed` — current MARADMIN cache
- `GET /message-watch/navadmins/feed` — NAVADMIN cache
- `GET /message-watch/alnavs/feed` — ALNAV cache
- `GET /message-watch/dod/feed` — DoD watch cache

**Refresh feeds if stale:**
- `POST /maradmins/refresh`
- `POST /message-watch/navadmins/refresh`
- `POST /documents/check-updates` — scan new messages against tracked doctrine

**Accept a reviewed candidate:**
- `POST /documents/source-states/accept/{candidate_id}`

**Mark a candidate reviewed:**
- `POST /documents/updates/{candidate_id}/status`

## Workflow

1. Pull all update candidates — separate new (unreviewed), reviewed, and ignored items.
2. Pull all verified source states — note what has been confirmed current and when.
3. Refresh the MARADMIN and message feeds if they look stale (compare last-fetched date to today).
4. Run `/documents/check-updates` against current feed items if new messages are available.
5. Triage the open candidates — for each, surface: what changed, which local references it may affect, and what action the user should take.
6. Flag references that are still in `needs_review` or `update_detected` state but are being relied on in current products.
7. Recommend which candidates to accept, which to mark ignored, and which need human verification before accepting.
8. If the user confirms a source is current, offer to accept it via `/documents/source-states/accept/{candidate_id}`.

## Output Format

- **Source trust summary** — counts: verified-current, needs-review, update-detected, ignored.
- **Open candidates requiring action** — each with: what flagged it, which references it affects, recommended action.
- **Verified-current references** — brief list with last-verified date.
- **Feed freshness** — how old each feed cache is; flag if stale.
- **Action queue** — ordered list of follow-up steps with the route to take for each.
- **Human verification triggers** — items that need the user to check the actual source before accepting.

## Safety And Review Rules

- Do not mark a source as verified-current without explicit user confirmation — the skill recommends acceptance, the user approves it.
- Distinguish between "feed item detected a change" and "source is confirmed updated" — these are different states.
- Flag when the local feed cache is older than 7 days and may not reflect the latest MARADMIN traffic.
- Keep all recommendations advisory — the user must verify against the actual official source before routing any product based on a reference.
- Do not claim a reference is outdated without evidence from a feed item or update candidate.

## Failure Modes

- Feed caches are empty — no MARADMINs have been pulled yet; recommend running a refresh first.
- No update candidates exist — the monitoring service hasn't been run; offer to run a check-updates pass.
- Update candidates are all in `ignored` state — the user marked things ignored without reviewing them; surface this.
- A candidate is accepted but the underlying source wasn't actually checked — outputs will still warn.

## Verification Checklist

- All open update candidates are surfaced with recommended action, not just listed.
- Feed freshness is checked and flagged if any cache is older than a week.
- Verified-current list includes last-verified date for each entry.
- Human verification triggers are explicit — not buried in the action queue.
- The skill did not accept any source state without user confirmation.
