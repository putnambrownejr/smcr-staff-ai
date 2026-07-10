# ADR-002: Validated One-Call Scenario Envelopes

## Status

Proposed

## Date

2026-07-10

## Context

Scenario-capable agents currently return readable text alongside default-empty structured models. The chain endpoint passes those empty shapes to downstream agents, so the apparent structured handoff does not carry the analysis.

The external provider could be called once for prose and again for structured extraction, but that doubles cost, latency, and disclosure events.

Provider-specific structured-output features are not consistently available across OpenAI-compatible endpoints.

## Decision

Each approved scenario call will request one provider-neutral JSON envelope containing:

- A non-empty readable answer.
- A role-specific scenario_output object.

The role-specific Pydantic JSON schema will be included in the prompt. A local parser will validate JSON shape, expected role, forbidden extra fields, and meaningful populated content.

Only validated scenario_output values may be passed to downstream agents.

If a single-agent envelope has an invalid structured object but a readable answer, the answer remains available with an invalid status and warning. If the envelope is malformed, the deterministic template is returned.

An externally processed chain stops before another outbound call when a required structured handoff is invalid. A local-only chain continues deterministic steps but clearly reports that no structured handoff occurred.

## Alternatives Considered

### Second extraction call

Pros:

- Separates prose generation from schema extraction.

Cons:

- Doubles network calls, cost, latency, and approval complexity.
- The second model can reinterpret rather than faithfully structure the first answer.

Rejected because one validated envelope is simpler and more auditable.

### Parse free-form Markdown heuristically

Pros:

- Keeps the current prose prompt.

Cons:

- Headings and lists vary across providers and responses.
- Heuristic extraction would silently produce partial or incorrect handoffs.

Rejected because the handoff contract needs explicit structure.

### Require provider-native JSON schema support

Pros:

- Strong generation-time schema enforcement where supported.

Cons:

- Breaks the project's OpenAI-compatible and local-provider flexibility.

Rejected as a mandatory dependency. It may be added later as an optional provider capability.

## Consequences

- Scenario prompts become stricter and return a JSON envelope rather than plain prose.
- The API distinguishes validated, invalid, template-only, and non-applicable structured states.
- Existing tests that assert only field presence must be replaced with value-propagation tests.
- Empty handoff shells are no longer presented as real structured analysis.
- Chains can return partial results with an explicit stop reason.

DRAFT — Verify all references against current official sources before acting.
