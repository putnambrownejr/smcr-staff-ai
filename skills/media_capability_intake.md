# Media Capability Intake

This note captures which capabilities from `smcr_uc_media_migration.bundle.*` were worth carrying into `smcr-staff-ai`.

These media artifacts are advisory local context, not canonical doctrine or official requirements.

## Pulled In

- `data merging / commonality analysis`
  - Added as `POST /analysis/merge-records`
  - Why it fits: reserve admin, billet matching, roster cleanup, source comparison, and cross-document reconciliation are all common SMCR pain points.

- `TDG generation`
  - Added as `POST /training/tdg`
  - Why it fits: low-cost PME and leader-development content is highly useful in drill-limited environments.

- `POA&M scaffold from higher guidance`
  - Added as `POST /staff-products/poam`
  - Why it fits: turning higher guidance into staff-section tasks, owners, and suspense structure is directly aligned with staff workflows.

## Already Covered Elsewhere

- `professional email drafting`
  - Already covered well enough by the correspondence conversion workflow:
    - `POST /personnel/convert-correspondence`
  - We did not add a separate duplicate email-only feature.

- `dashboard shortcuts`
  - Interesting, but intentionally deferred because the current priority is backend maturity over more dashboard surface area.

## Intentionally Not Imported Directly

- platform-specific `APEX` or `Moodle` support
  - Useful pattern, but too environment-specific for the current repo scope.

- workbook-centric logic that assumes a specific AI platform storage model
  - We pulled the useful capability shape, not the platform mechanics.

## SMCR Read

The strongest value from these videos was not the exact UI or platform used. It was the workflow pattern:

1. start from rough user intent
2. structure the problem quickly
3. produce a draft or candidate output
4. require human validation
5. preserve useful local context for follow-on work

That pattern is now reflected in the backend much more strongly than before.
