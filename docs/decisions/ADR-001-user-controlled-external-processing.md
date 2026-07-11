# ADR-001: Preview-Bound User Control for External Processing

## Status

Accepted

## Date

2026-07-10

## Context

The application is local-first but can optionally call an OpenAI-compatible external provider for scenario assessment population. The current call path can transmit user input before shared warning logic runs.

Training scenarios can contain terms that resemble sensitive operational material. Pattern detectors cannot determine actual classification, handling authority, or whether a match is a harmless exercise false positive. Treating every match as a hard block would make legitimate training workflows unreliable.

The application still needs to prevent silent disclosure and make the outbound choice inspectable.

## Decision

Every prospective external scenario request will pass through a preview-bound approval flow.

The application will:

- Build the complete prospective outbound payload before any network call.
- Show the provider, model, expected call count, findings, original preview, and sanitized preview.
- Treat all detector findings as advisory warnings rather than classification decisions.
- Offer local-only, sanitized, and original disclosure modes.
- Require explicit acknowledgement before either external mode.
- Bind single-agent approval to a SHA-256 digest of both exact displayed outbound candidates and immutable request metadata; record the selected mode separately.
- Bind chain approval to the immutable workflow contract because later generated handoffs do not exist at preview time.
- Recompute and compare the applicable approval digest immediately before sending.
- Rescan each later chain payload, apply the selected disclosure mode, and record a step-specific payload digest separately from the chain approval digest.
- Store only metadata about the decision and outcome.

The acknowledgement confirms that the user is authorized to disclose the material, that it is appropriate for the selected provider, and that it complies with the project's UNCLASSIFIED-only handling rule.

The application does not claim that the acknowledgement proves the content's classification or legal handling status.

## Alternatives Considered

### Hard-block every detector match

Pros:

- Strong technical prevention for recognized patterns.

Cons:

- High false-positive cost for realistic training scenarios.
- Regex cannot determine actual classification or authorization.
- Encourages users to rewrite around the detector without improving disclosure judgment.

Rejected because it makes the heuristic act as an authority it cannot be.

### Warn but send immediately

Pros:

- Minimal implementation effort.

Cons:

- The user cannot inspect the exact outbound data before disclosure.
- Warnings can occur after the consequential action.
- No protection against request changes between warning and send.

Rejected because informed choice must precede the network call.

### Disable all external processing

Pros:

- Strongest local-only privacy posture.

Cons:

- Removes the scenario-population capability the user wants.
- Does not support deliberate use of approved external or local-compatible providers.

Rejected because explicit, inspectable opt-in meets the product need.

## Consequences

- External calls require an additional preview and approval round trip.
- API clients must handle HTTP 409 when approval is missing or stale.
- Detector warnings remain useful without becoming hard classification gates.
- Users retain responsibility for disclosure decisions.
- Consent audit data can demonstrate that a decision occurred without retaining sensitive prompt content.
- The LLM client must accept only approved payload objects.
- A chain preview cannot display future generated handoffs; it must clearly describe how they will be rescanned and disclosed.

DRAFT — Verify all references against current official sources before acting.
