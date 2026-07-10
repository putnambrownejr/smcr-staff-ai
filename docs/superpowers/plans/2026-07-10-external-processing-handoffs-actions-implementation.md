# External Processing, Structured Handoffs, and Action Completion Implementation Plan

Status: Implemented and verified on 2026-07-10.

Design source: docs/superpowers/specs/2026-07-10-external-processing-handoffs-actions-design.md

## Phase 1: External-processing contracts

Files:

- app/schemas/external_processing.py
- app/schemas/agents.py
- app/schemas/scenario_handoff.py
- app/core/security.py
- tests/test_external_processing.py

Work:

- Add disclosure-mode, preview, approval, finding, audit, and scenario-output-status models.
- Add warning-only finding extraction and redaction helpers.
- Add canonical payload hashing.
- Add unit coverage for original and sanitized payloads, acknowledgements, and stable digests.

Exit check:

- No network-capable function is involved in preflight tests.
- Every finding remains overridable after acknowledgement.

## Phase 2: Preflight service and audit store

Files:

- app/services/external_processing/preflight.py
- app/services/external_processing/audit_store.py
- app/core/config.py
- tests/test_external_processing.py

Work:

- Build original and sanitized outbound payloads.
- Derive provider-safe display metadata.
- Persist metadata-only audit entries with a 200-entry cap.
- Verify audit serialization never includes prompt text, previews, keys, headers, or responses.

Exit check:

- Audit tests scan serialized files for synthetic secret and prompt markers.

## Phase 3: Approved LLM boundary and preview routes

Files:

- app/services/llm_client.py
- app/api/routes/agents.py
- app/services/agents/staff_advisor_agent.py
- app/services/agents/planning_advisor_agent.py
- app/services/agents/chief_of_staff_agent.py
- tests/test_llm_scenario_inference.py
- tests/test_agents_route.py

Work:

- Change the LLM client to accept only an approved outbound payload.
- Add single-agent and chain preview endpoints.
- Enforce local_only, sanitized, original, acknowledgement, and stale-digest behavior.
- Ensure no-key and non-scenario requests remain deterministic without approval.
- Cover every path with mocked HTTP clients.

Exit check:

- A regression test proves raw scenario input cannot reach the HTTP client without current approval.

## Phase 4: Validated scenario envelopes

Files:

- app/services/agents/scenario_envelope.py
- app/schemas/scenario_handoff.py
- app/schemas/agents.py
- app/api/routes/agents.py
- scenario-capable agent files
- tests/test_scenario_handoff.py
- tests/test_llm_scenario_inference.py

Work:

- Request one JSON envelope containing answer and scenario_output.
- Validate expected role, strict fields, and meaningful content.
- Return explicit scenario-output status.
- Pass only validated values downstream.
- Stop externally processed chains before the next call after invalid structured output.
- Keep local-only chains deterministic without fake structured handoffs.

Exit check:

- A full mocked chain asserts concrete values are visible in downstream prompts.
- Invalid output prevents the next mocked network call.

## Phase 5: Consent dialog

Files:

- app/static/dashboard/index.html
- app/static/dashboard/dashboard.js
- app/static/dashboard/dashboard.css
- tests/test_dashboard.py
- tests/e2e/test_dashboard_flows.py

Work:

- Add the reusable preview dialog.
- Show provider, model, call count, findings, and both previews.
- Support local template, sanitized send, and original send.
- Require acknowledgement for either external choice.
- Resubmit the original operation with the approved digest and mode.

Exit check:

- Keyboard and screen-reader state are testable.
- Cancelling or choosing local-only makes no external request.

## Phase 6: Action module and Undo

Files:

- app/static/dashboard/actions.js
- app/static/dashboard/dashboard.js
- app/static/dashboard/index.html
- app/static/dashboard/dashboard.css
- tests/e2e/test_dashboard_flows.py

Work:

- Load dashboard.js as a native module and remove the remaining inline onclick handler.
- Extract tracked-action rendering and interaction.
- Add optimistic Mark done behavior with per-item ten-second Undo.
- Restore the prior status and focus on Undo.
- Restore the row on API failure.
- Keep demo mode read-only.

Exit check:

- Browser tests cover success, backend closed state, Undo, prior-status restoration, and PATCH failure.

## Phase 7: Documentation reconciliation

Files:

- README.md
- .env.example
- ARCHITECTURE.md
- docs/core_documents/roadmap.md
- docs/HOW_TO_USE.md
- docs/compatibility/external_ai_safe_use.md
- docs/API_REFERENCE.md
- docs/improvement-backlog.md

Work:

- Describe runtime external processing accurately.
- Document warning-only findings and user-owned disclosure decisions.
- Document preview endpoints and response-status fields.
- Record action completion and the bounded module split.

## Phase 8: Verification

Run:

- Targeted tests after each phase.
- uv run pytest tests/ -q
- uv run mypy app tests
- uv run ruff check .
- E2E tests with the local server running.

Report pre-existing failures separately and introduce no new failures in changed files.

## Verification Results

- `uv run pytest tests/ -q -m "not e2e"`: 516 passed, 6 deselected.
- `uv run pytest -m e2e tests/e2e/ -q`: 7 passed, 1 intentionally manual test skipped.
- Targeted external-processing, handoff, dashboard, and config suite: 50 passed.
- `node --check` passed for `dashboard.js` and `actions.js`.
- Ruff passed on all changed Python and test files.
- Full Ruff remains blocked by the pre-existing import-order finding in
  `app/services/agents/registry.py`.
- Full mypy remains blocked by pre-existing strict-typing debt in unrelated files and
  the existing untyped Playwright test scaffold. The two new structured-handoff indexing
  findings were corrected.

DRAFT — Verify all references against current official sources before acting.
