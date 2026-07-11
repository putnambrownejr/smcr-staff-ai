# External Processing, Structured Handoffs, and Action Completion Design

Status: Approved on 2026-07-10.

Date: 2026-07-10

## Purpose

This design covers three connected improvements:

1. Make optional external LLM processing explicitly user-controlled and previewable.
2. Replace empty scenario handoff shells with validated, populated structured data.
3. Add action completion with Undo while extracting the action UI from the dashboard monolith.

The work is one coordinated vertical slice. It does not redesign unrelated agents, storage domains, or dashboard lanes.

## Context

The current optional LLM path sends scenario input before the shared sensitive-input warning is applied. The safety detector therefore informs the response after the outbound decision has already occurred.

Scenario agents can return useful prose, but their scenario_output values are default-empty Pydantic models. The chain endpoint passes those empty shapes forward, so downstream agents do not receive the analysis that the user sees.

The dashboard renders tracked actions as read-only rows even though the backend already supports status updates. The main dashboard script is also beyond its documented module-split threshold.

## Confirmed Product Decisions

- External processing is opt-in for every single-agent request or agent-chain request.
- The user sees the proposed outbound content, provider, model, findings, and expected call count before approval.
- Findings are advisory warnings. They are not classification determinations and never become an automatic hard block.
- The default outbound choice is the sanitized preview.
- The user may send the original text after explicit acknowledgement.
- The acknowledgement states that the user confirms the material is appropriate and authorized for the selected external provider and complies with the project's UNCLASSIFIED-only handling rule.
- The application does not claim to determine whether material is actually classified, CUI, COMSEC, PII, or otherwise restricted.
- One external response contains both the readable assessment and role-specific structured data.
- Only validated, meaningfully populated structured data may pass to a downstream agent.
- Marking an action done removes it immediately and offers a ten-second Undo action.
- The dashboard split is limited to action rendering and behavior in this change.

## Goals

- Prevent any external LLM call without a preview-bound user decision.
- Preserve user control when heuristic detectors produce false positives on training material.
- Make the exact disclosure mode visible: local-only, sanitized, or original.
- Detect stale approval when the request, provider, model, or outbound payload changes.
- Keep raw scenario content, previews, API keys, and model responses out of the consent audit.
- Populate structured scenario models with actual assessment data.
- Stop an externally processed chain before another outbound call when a required structured handoff is invalid.
- Preserve deterministic template behavior when no LLM is configured.
- Add accessible, reversible action completion to personal workspaces.
- Preserve the no-build, offline-capable frontend.

## Non-Goals

- Determining the true classification or legal handling status of user content.
- Replacing user or organizational disclosure review.
- Automatically approving any external disclosure.
- Persisting outbound previews or raw prompt content.
- Adding provider-specific structured-output dependencies.
- Rewriting the entire dashboard or introducing a frontend framework.
- Implementing semantic RAG, live connectors, or a general workflow engine.
- Fixing unrelated pre-existing mypy or Ruff findings.

## Architecture Overview

The implementation adds three bounded components:

1. ExternalProcessingPreflightService builds, scans, sanitizes, hashes, and describes the prospective outbound payload.
2. ScenarioEnvelopeParser validates the one-call narrative-plus-structured response against the expected role model.
3. TrackedActionsController owns action-row rendering, completion, failure restoration, and Undo behavior.

Existing agent classes remain responsible for domain prompts and deterministic templates. Existing action routes remain the persistence API.

## 1. External-Processing Privacy Boundary

### Request and response models

Add the following models in a dedicated external-processing schema module:

- DisclosureMode: local_only, sanitized, or original.
- ExternalProcessingFinding: category, severity, message, and detected field path.
- ExternalProcessingPreview: whether external processing is available and required; provider host; model; expected call count; original preview; sanitized preview; warnings; finding categories; redacted fields; and approval digest.
- ExternalProcessingApproval: disclosure mode, approval digest, acknowledged finding categories, and an explicit acknowledgement boolean.
- ExternalProcessingAuditEntry: timestamp, user key digest or local default key, agent or chain identifier, provider host, model, disclosure mode, finding categories, approval digest, and call count.

AgentRunRequest gains an optional external_processing_approval field.

ChainRequest gains the same optional field. A chain approval digest covers the scenario, selected context, ordered step definitions, provider, model, and the explicit workflow rule that validated generated assessments will be provided to later agents. The selected disclosure mode is stored alongside that digest in the approval and audit record. Later generated text cannot be previewed before the chain starts, so it is not represented as though it were part of the initial exact-text preview.

### Preview endpoints

Add:

- POST /agents/{agent_id}/external-processing-preview
- POST /agents/chain/external-processing-preview

The single-agent preview accepts the same input and context as AgentRunRequest, excluding any prior approval.

The chain preview accepts the scenario, ordered steps, and context.

If no API key is configured, or the request will not use scenario-mode inference, the response reports that external processing is not required and the normal deterministic path can run.

### Preview construction

The preflight service builds both candidate payloads before any network call:

- Original: the exact user-provided and locally assembled content that would be sent.
- Sanitized: the same content after existing PII patterns and sensitive-content patterns replace matched spans with explicit redaction markers.

Scanning covers:

- User scenario input.
- Active local context included by the agent.
- Prior structured assessments.
- Role template additions that contain local data.

The visible preview focuses on disclosed user and local-context content. It does not expose API keys or internal credentials.

For a single-agent request, the approval digest is SHA-256 over a canonical JSON representation of both displayed candidates and their immutable request metadata: provider base URL, model, original messages, sanitized messages, agent scope, and call count. The user may therefore choose either displayed candidate using the same preview digest; the selected disclosure mode is an explicit, separately recorded approval field.

For a chain, the approval digest binds the immutable workflow contract rather than unknowable future generated text. Before every chain step, the server rescans the current payload, applies the approved disclosure mode to scenario, local-context, and generated-prior-assessment content, and records a separate step payload digest. Sanitized mode redacts newly detected spans in generated handoffs. Original mode passes generated handoffs as produced. The preview states this distinction explicitly.

### User decisions

The reusable dashboard dialog offers exactly three actions:

1. Use local template: make no network call.
2. Send sanitized: send the sanitized payload after acknowledgement.
3. Send as written: send the original payload after acknowledgement.

Findings never disable either external send option. They explain why the user should review the preview.

The acknowledgement states:

I understand this content will be sent to the named external provider. I confirm that I am authorized to disclose it, that it is appropriate for external processing, and that it complies with this project's UNCLASSIFIED-only handling rule.

The application records that acknowledgement as metadata. It does not treat the acknowledgement as proof of classification or authority.

### Enforcement

The run path recomputes the candidate payload and digest immediately before calling the LLM client.

- Missing approval when external processing would occur returns HTTP 409 with the current preview.
- A mismatched digest returns HTTP 409 with a fresh preview.
- Unacknowledged current finding categories return HTTP 409.
- local_only bypasses the LLM and returns the deterministic template.
- sanitized sends only the recomputed sanitized payload.
- original sends only the recomputed original payload.

The LLM client accepts only a preflight-approved payload object. It no longer accepts arbitrary raw user text from agent code. This makes bypassing preflight difficult by construction.

### Audit storage

Use the existing per-user JSON-store pattern under a new external_processing_audits storage directory.

Each audit file retains the newest 200 metadata entries. It stores:

- Timestamp.
- Agent ID or ordered chain IDs.
- Provider hostname and model.
- Disclosure mode.
- Finding categories.
- Approval digest.
- Expected and completed call counts.
- Outcome: completed, failed, local_only, or stale.

It never stores raw prompts, previews, matched text, API keys, authorization headers, or model responses.

## 2. Validated Scenario Envelopes

### One-call response contract

Every scenario-capable external call requests a single JSON object with:

- answer: non-empty readable assessment text.
- scenario_output: the role-specific structured object.

The system prompt includes the expected role's Pydantic-generated JSON schema and tells the provider to return only the envelope.

The implementation remains provider-compatible by using prompt-enforced JSON rather than requiring a provider-specific response-format feature. A single surrounding Markdown code fence may be stripped before parsing. No automatic repair call is made.

### Validation

Create ScenarioEnvelopeParser with the expected scenario-output model supplied by the agent.

Validation requires:

- Valid JSON object.
- Non-empty answer.
- Expected role value.
- No unexpected fields at any scenario schema level.
- At least one meaningful populated value outside role and planning tempo.

A value such as "Not specified in scenario — requires collection" is meaningful because it communicates an assessed gap. Empty strings, empty lists, empty dictionaries, null values, role, and tempo alone do not satisfy the meaningful-content rule.

### Response status

Add ScenarioOutputStatus to AgentRunResponse:

- not_applicable: the request did not use scenario mode.
- template_only: deterministic template returned without structured inference.
- validated: populated scenario_output passed validation.
- invalid: external output was attempted but a valid handoff was unavailable.

scenario_output is non-null only when status is validated.

This intentionally replaces the current behavior where template runs return default-empty handoff objects.

### Failure behavior

For a single-agent call:

- Valid envelope and valid handoff: return answer plus structured output.
- Valid envelope but invalid handoff: return the readable answer, set status invalid, and add a prominent warning.
- Malformed envelope: return the deterministic template, set status invalid, and add a warning describing the parse failure without exposing provider internals.

For an externally processed chain:

- Pass only validated scenario_output values into prior_assessments.
- If a step's required structured output is invalid, return completed results and stop before the next external call.
- Add completed, stopped_at_agent_id, and stopped_reason fields to ChainResponse.

For a local-only or no-key chain:

- Run the requested deterministic templates without fabricated structured handoffs.
- Mark each scenario-capable result template_only.
- Explain that the steps ran independently because no validated structured handoff was produced.

### Tests

Tests must verify values, not only field presence:

- Each supported role parses a populated envelope.
- Wrong-role, extra-field, malformed, and all-empty outputs fail validation.
- A full G-9 to S-2 to Planning to Chief chain passes specific values forward.
- Downstream prompts contain prior validated values.
- Invalid external output stops the chain before another mocked network call.
- Template-only runs return scenario_output null.
- Existing non-scenario agent behavior remains unchanged.

## 3. Action Completion and Dashboard Module Split

### Module boundary

Create app/static/dashboard/actions.js as a native ES module exporting TrackedActionsController.

Change the dynamic dashboard loader to load dashboard.js with type module. dashboard.js imports the controller from ./actions.js.

Replace the remaining inline history-fact onclick handler with an event listener before relying on module scoping.

Only action-list rendering and interaction move in this change. State, API helpers, and other lane renderers remain in dashboard.js.

### Controller dependencies

The controller receives explicit dependencies:

- Target action-list element.
- Undo status-region element.
- API request callback.
- Workspace-refresh callback.
- Notification callback.
- HTML escaping and empty-state rendering callbacks.
- Function reporting whether the current workspace is personal and writable.

This keeps the module testable and avoids importing the entire dashboard state.

### Completion flow

Personal-workspace rows include an accessible Mark done button.

On click:

1. Save the item's prior status and current list position.
2. Remove the row immediately.
3. Send PATCH /actions/{action_id} with status closed.
4. On success, add a ten-second Undo notice and move keyboard focus to its Undo button.
5. On failure, restore the row in its previous position, restore focus, and announce the error.

Each completed item receives its own Undo notice and timer, so rapid completion of several actions does not discard earlier Undo opportunities.

Undo sends PATCH with the exact prior status, refreshes the workspace, removes the notice, and moves focus to the restored action's Mark done button.

Demo-mode rows do not show mutation controls. A concise note explains that action updates require a personal workspace.

### Accessibility and motion

- Buttons use descriptive accessible names containing the action title.
- Completion and failure messages use an aria-live status region.
- Focus never disappears with the removed row.
- Existing focus-visible styling applies.
- Any removal transition is disabled under prefers-reduced-motion.

### Tests

Add a Playwright flow that:

1. Creates a tracked action through the API.
2. Loads the matching personal workspace.
3. Marks the action done.
4. Confirms it leaves the active queue and an Undo control appears.
5. Confirms the backend status is closed.
6. Selects Undo.
7. Confirms the prior status and visible row return.

Add a failure-path browser test using a mocked PATCH failure to confirm that the row is restored and the error is announced.

Existing backend tests continue to verify action history, filtering, and closed-status behavior.

## Documentation Changes During Implementation

Update:

- README.md and .env.example for the explicit preview and approval flow.
- ARCHITECTURE.md and the roadmap to remove absolute no-runtime-LLM contradictions.
- docs/HOW_TO_USE.md and docs/compatibility/external_ai_safe_use.md.
- docs/API_REFERENCE.md for preview, approval, response-status, and chain-stop fields.
- docs/improvement-backlog.md to record action completion and the first dashboard module split.

The documentation must state that detector findings are advisory and that the user owns the disclosure decision.

## Backward Compatibility

- With no LLM key, normal single-agent template behavior remains available without approval.
- Non-scenario agent requests do not require preflight.
- With an LLM key, API clients must choose local_only, sanitized, or original before an outbound call.
- AgentRunResponse gains a status field.
- Existing empty scenario_output objects become null unless a validated handoff exists.
- ChainResponse gains completion and stop metadata.
- No existing user JSON store requires migration.

## Verification

Run:

- uv run pytest tests/ -q
- uv run mypy app tests
- uv run ruff check .
- uv run pytest -m e2e tests/e2e/ -q with the server running

Changed files must introduce no new mypy or Ruff errors. Any unrelated pre-existing failures will be reported separately.

## Implementation Sequence

1. Add external-processing schemas, preflight service, audit store, and tests.
2. Route every scenario LLM call through preflight-approved payloads.
3. Add preview endpoints and approval enforcement for single and chain requests.
4. Add the reusable approval dialog to the dashboard.
5. Add scenario envelope parsing, strict validation, and response status.
6. Update chain propagation and stop behavior.
7. Extract actions.js and add Mark done plus Undo.
8. Add API, unit, and browser regression coverage.
9. Reconcile public documentation and run the complete verification suite.

DRAFT — Verify all references against current official sources before acting.
