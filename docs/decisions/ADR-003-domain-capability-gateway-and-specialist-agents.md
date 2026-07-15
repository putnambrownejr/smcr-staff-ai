# ADR-003: Use a Domain Capability Gateway and Bounded Specialist Agents

## Status

Accepted

## Date

2026-07-15

## Context

SMCR Staff AI needs a Chief of Staff experience that can answer questions across the application and carry out low-friction user requests. The same release adds Travel/GTCC tracking, FitRep analytics, unit fitness planning, financial readiness, Marine Leader Development, and philosophical reflection.

A generic repository/filesystem tool would be easy to expose to the Chief of Staff, but it would bypass domain validation, user-key scoping, review requirements, Undo behavior, and safeguards around sensitive local data. Combining all new subjects into one large agent would also obscure which source pack, safety boundary, and professional limitation applies to a response.

## Decision

The Chief of Staff coordinates the application through typed, user-key-scoped domain capabilities. Approved append operations may execute immediately and return an Undo action. Inferred imports, replacements, deletions, external transmission, and bulk changes require review or explicit confirmation according to their risk.

Repository awareness is provided through a read-only, repository-root-scoped search capability with explicit exclusions for secrets, environment files, VCS internals, credential stores, caches, and paths outside approved roots. The Chief of Staff does not receive an arbitrary shell or generic filesystem writer.

Specialist agents remain separate where their authority and safety boundaries differ:

- GTCC Advisor handles official travel-card workflows.
- Financial Readiness Advisor handles personal financial education.
- Fitness Planning Advisor owns physical programming and synthesizes structured S-3, S-4, SEL, and ORM reviews.
- Leadership Advisor owns practical Marine Leader Development and the six functional areas.
- Warrior-Monk owns philosophical reflection and may hand actionable goals to Leadership Advisor.

Agent-to-agent planning uses typed handoff schemas. Free-form text remains presentation content, not the integration contract.

## Alternatives Considered

### Give the Chief of Staff unrestricted repository and filesystem access

- Pros: Broad capability with little domain-specific implementation.
- Cons: Weak validation, unclear audit trail, accidental access to secrets or unrelated files, and no reliable review/Undo semantics.
- Rejected: It conflicts with the local-first privacy model and makes safe domain behavior difficult to verify.

### Combine GTCC and personal financial readiness

- Pros: Fewer agent cards and some shared money vocabulary.
- Cons: Blurs an official travel-card program with personal finance, encourages inappropriate balance aggregation, and complicates source/safety boundaries.
- Rejected: The agents may hand off explicitly but retain separate data and responsibilities.

### Combine Leadership Advisor and Warrior-Monk

- Pros: One entry point and shared sources.
- Cons: Practical counseling and MLD workflows would be mixed with reflective philosophical dialogue, making both roles less predictable.
- Rejected: They share a source foundation and handoff path while keeping distinct user promises.

### Pass prose between Fitness, S-3, S-4, SEL, and ORM

- Pros: Minimal schema work.
- Cons: Brittle parsing, missing-field ambiguity, weak validation, and difficult partial-failure recovery.
- Rejected: A structured `UnitPtPlan` and typed review outputs provide stable contracts.

## Consequences

- New domain operations require schemas, stores/services, routes, and authorization dependencies before the Chief of Staff can invoke them.
- Users receive explicit provenance, confirmation, and Undo behavior instead of opaque repository mutations.
- Agent cards remain more numerous, but each card communicates a narrower and more trustworthy scope.
- Cross-agent workflows can return partial results and identify missing reviews without discarding completed work.
- Future domains should add bounded capabilities rather than expanding a generic Chief of Staff filesystem tool.

DRAFT — Verify all references against current official sources before acting.
