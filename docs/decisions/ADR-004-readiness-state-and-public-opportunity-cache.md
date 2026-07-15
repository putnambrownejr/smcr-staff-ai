# ADR-004: Separate readiness state from the public opportunity cache

## Status

Accepted

## Date

2026-07-15

## Context

Family-readiness checklists contain user-entered progress, contacts, and broad absence windows. Career opportunities are public records sourced from MARFORRES gateways and may be reused across local users. The official MARFORRES pages can also return HTTP 403 to non-browser clients even while remaining available to a user in a browser.

The dashboard must remain local-first, avoid unnecessary PII, never replace parser failures with sample listings, and preserve the last successful public result when a source changes or becomes unavailable.

## Decision

- Store each family-readiness event under a user-key-derived path. Treat the typed event record—not a generated summary—as canonical state.
- Export only generic milestones to calendars and redact private or non-shareable fields from spouse-friendly summaries.
- Store career-opportunity refresh results once per allowlisted public source, separate from user-scoped tracking or preferences.
- Accept only registered official source keys. Do not accept arbitrary refresh URLs from clients.
- Refresh sources independently. On failure, retain and label the last successful cache; without a cache, show the official link and a truthful failure state.
- Never substitute fixtures, infer missing dates or eligibility, authenticate to DoD systems, or auto-apply.

## Alternatives Considered

### Store readiness in free-form generated documents

Rejected because checklist status, sharing controls, contacts, and milestone dates require typed validation and reliable updates. Generated documents remain appropriate only for shareable outputs.

### Scope the public opportunity cache to each user

Rejected because it duplicates identical public data and makes refresh state inconsistent. Only user actions such as tracking remain user-scoped.

### Scrape through browser automation or add a background crawler

Rejected for the first version because it adds runtime dependencies, can still fail against anti-automation controls, and conflicts with the local-first, explicit-refresh design.

### Show test fixtures when live extraction fails

Rejected because sample billets could be mistaken for current opportunities. Parser failure is not evidence that no billets exist and is not permission to invent listings.

## Consequences

- Family readiness data remains private to the local user key and can be removed independently.
- Career refreshes are efficient and consistent across users on the same installation.
- A successful parser result can be sorted and filtered without mutating the cache.
- Some refreshes will show link-only or cached states when MARFORRES blocks automated requests; the user still has a one-click official source path.
- New sources require an explicit registry entry, parser tests, and a security review of allowed hosts and content types.

Official source baseline, verified 2026-07-15:

- [MARFORRES Reserve Billets](https://www.marforres.marines.mil/About/Reserve-Billets/)
- [MARFORRES Active Billets / Find](https://www.marforres.marines.mil/Staff-Sections/General-Staff/G-1-Administration/Active-Billets/Find/)

DRAFT — Verify all references against current official sources before acting.
