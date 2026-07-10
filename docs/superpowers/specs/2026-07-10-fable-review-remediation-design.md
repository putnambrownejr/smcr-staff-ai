# Fable Review Remediation Design

Status: Implemented and verified on 2026-07-10.

## Context

Claude's post-commit Fable review of `4544b8c` found no critical or high-severity
issues, but identified two medium findings and a bounded group of low-severity
hardening and quality-gate findings. The implementation is already published on
`codex/external-processing-handoffs-actions` in draft PR #26.

The user selected one comprehensive follow-up rather than separate blocker and polish
commits. This design keeps that follow-up narrow: repair confirmed defects, make the
repository's documented quality gates honest, and avoid a broader agent-capability
refactor.

## Goals

- Prevent ordinary words such as `support`, `broadcast`, and `Indianapolis` from
  accidentally activating scenario mode.
- Ensure detector-warning overrides come from a preflight-validated external approval,
  not a caller-supplied acknowledgement boolean by itself.
- Make approved external-call failures visible in normal server logs without recording
  prompt or response content.
- Recover safely when a metadata-only external-processing audit file is malformed.
- Describe chain call counts conservatively and accurately as an upper bound.
- Avoid running an advisory agent once for preview and again for execution when no
  external provider is configured.
- Remove approval-dialog listener accumulation and repeated chain warnings.
- Make the documented Ruff and mypy commands pass across the repository.
- Deliver regression coverage and one comprehensive follow-up commit to PR #26.

## Non-Goals

- Adding new agents, disclosure modes, providers, or UI workflows.
- Adding expiry to approval digests; the accepted localhost replay trade-off remains
  documented in ADR-001.
- Adding formal external-processing capability metadata to every agent.
- Removing the preview pass when an external provider is configured. In that mode the
  server must still determine whether the specific request would use scenario inference.
- Reworking unrelated application behavior while resolving mechanical type debt.

## Approach Selected

Use targeted fixes plus full quality-gate closure.

This approach is broader than patching only the lines named in the review because a
partial mypy cleanup would leave the repository's documented command failing. It is
narrower than introducing a new capability model across the agent registry.

## Detailed Design

### 1. Token-aware scenario detection

Replace bare substring membership with one shared token-bound matcher. Each configured
signal is escaped before use and must be surrounded by non-word boundaries. Multi-word
signals remain supported.

Regression cases will prove:

- `support` does not match `port`.
- `broadcast` does not match `road`.
- `workmanship` does not match `km`.
- `Indianapolis` does not match `india`.
- Genuine scenario text containing a scenario signal plus a country or concrete detail
  still activates scenario mode.

### 2. Preflight-derived warning override

The three scenario-capable agent paths currently derive `allow_warning_override` from
the raw request model. Replace that with a boolean carried by the scenario-generation
result and scenario-population result.

The boolean becomes true only after preflight successfully validates a non-local
approval digest, acknowledgement, and all current finding categories. `local_only`
continues to make no external call but does not suppress the generic sensitive-input
response merely because a caller set `acknowledged: true`.

This preserves the approved user choice to send sanitized or original content after
explicit acknowledgement while closing the raw-model bypass.

### 3. External-call logging

Change the approved-call failure log from debug to warning. Keep exception information
for local diagnosis, but do not add prompt text, response bodies, API keys, headers, or
other disclosure content to the message.

### 4. Corrupted audit recovery

When Pydantic rejects an existing audit JSON file, rename that file beside the original
using a timestamped `.corrupt-*` suffix and return a new empty audit log. The next append
then writes a valid primary file.

Only validation/decoding corruption is recovered automatically. General filesystem
permission or I/O failures remain visible rather than being silently discarded.

### 5. Chain count and warning presentation

Keep `expected_call_count` as the conservative maximum represented by the requested
steps, avoiding a public schema rename. Change the dashboard label and preview warning
language to say `Up to N external calls`.

Deduplicate accumulated chain warnings while preserving first-seen order. This removes
repeated baseline warnings without hiding distinct step-specific warnings.

### 6. Preview execution efficiency

In the single-agent and chain preview routes, return the existing no-external preview
immediately when `LLM_API_KEY` is not configured. This prevents a deterministic agent
from being run during preview and then run again during execution in the default local
configuration.

When a provider is configured, retain the preview execution because scenario detection
and the exact outbound payload are request-dependent.

### 7. Dialog lifecycle

Use a named cancel handler and remove it from the dialog inside the shared `finish`
function regardless of whether the user cancels or chooses a button. Existing settled
guards, focus behavior, and disclosure choices remain unchanged.

### 8. Quality-gate closure

- Add explicit return and parameter annotations to the Playwright fixture, helpers,
  route handlers, and tests.
- Add a narrow mypy override only for the untyped third-party Playwright import if
  necessary; do not disable strict checking for the E2E modules themselves.
- Resolve every remaining repository mypy finding with type guards, precise generic
  arguments, or generator annotations. Do not use broad `# type: ignore` comments when
  the type can be expressed.
- Correct the pre-existing registry import ordering so full Ruff passes.

Mechanical typing fixes must not alter runtime behavior.

## Error Handling

- Scenario detection remains deterministic and fails closed to normal advisory mode.
- Invalid or stale external approval continues returning HTTP 409 with a fresh preview.
- Audit corruption recovery never sends data externally and never copies audit content
  into logs.
- No-key preview short-circuit returns the same response model used today.
- Filesystem failures outside parse/validation corruption continue surfacing normally.

## Testing

Add or update tests for:

- Scenario false positives and genuine positives.
- Raw `local_only` acknowledgement not enabling warning override.
- Validated external approval still enabling warning override.
- Warning-level logging on an approved HTTP failure.
- Corrupted audit quarantine and successful subsequent append.
- No-key preview routes not invoking agent execution.
- `Up to N` dashboard language.
- Stable-order chain warning deduplication.
- Repeated approval-dialog opens without stale cancel handlers.

Run:

- `uv run pytest tests/ -q -m "not e2e"`
- `uv run mypy app tests`
- `uv run ruff check .`
- `node --check app/static/dashboard/dashboard.js`
- `node --check app/static/dashboard/actions.js`
- `uv run pytest -m e2e tests/e2e/ -q` with the local server running
- `git diff --check`

## Delivery

All remediation code, tests, mechanical typing fixes, and this design record will be
included in one comprehensive follow-up commit on
`codex/external-processing-handoffs-actions`, then pushed to draft PR #26.

## Acceptance Criteria

- All confirmed Fable findings are fixed or explicitly retained as an accepted,
  documented trade-off.
- Full pytest, mypy, Ruff, JavaScript syntax, and automated E2E checks pass.
- No secrets, raw external payloads, response bodies, or audit content are added to
  logs or tracked files.
- The working tree is clean after the commit and the remote PR contains the update.

DRAFT — Verify all references against current official sources before acting.
