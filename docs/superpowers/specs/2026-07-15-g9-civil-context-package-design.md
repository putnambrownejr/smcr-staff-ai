# G-9 Civil Context Package Design

**Date:** 2026-07-15

**Status:** Approved

**Scope:** Event-scoped civil-military planning support for domestic support and overseas/partner exercises.

## Purpose

Extend the existing G-9 planning workflow with two structured, source-aware subsections: infrastructure dependencies and cultural context. The feature creates a useful planning worksheet and a civil-estimate outline for one exercise or event; it does not create a persistent area-study or civil-environment record.

## Global Constraints

- UNCLASSIFIED information only. Do not accept CUI, precise operational locations, sensitive infrastructure vulnerabilities, movement details, call signs, frequencies, COMSEC material, or unnecessary PII.
- The feature is advisory planning support, not an intelligence product, targeting product, cultural authority, or approved engagement plan.
- Inputs and outputs remain request-scoped; no user-entered civil context or source items are persisted in v1.
- No runtime cloud dependency is introduced. Public-source research remains user supplied or uses the existing approved external-processing flow.
- Every response includes the existing default warnings and the footer: `DRAFT — Verify all references against current official sources before acting.`
- Sourced observations, analytic inferences, planning assumptions, and synthetic exercise content are visibly distinct.
- Domestic support and overseas/partner exercise framing are never blended. The response calls out the applicable context and routes users to confirm current legal, command, and coordination guidance.

## Existing Foundation

`G9PlanningRequest` currently captures an event title, supported problem, audience, partner types, civil considerations, and constraints. `G9Planner` returns civil situation, partner coordination, information requirements, engagement considerations, and continuity/transition prompts through `POST /staff/g9-plan`.

The new package extends that request/response rather than adding a standalone agent, store, route, or dashboard lane. This retains the G-9/Civil-Military ownership boundary and avoids duplication with the public-source OSINT agent, source-verification service, and source-trust review skill.

## User Inputs

### Operational context

The request adds `operating_context` with exactly two values:

- `domestic_support`: a domestic emergency-management, DSCA, or interagency exercise frame.
- `overseas_partner`: an overseas, coalition, host-nation, humanitarian, or partner-exercise frame.

New UI/API submissions must select a context. To preserve the existing minimal API contract, legacy callers may omit it; their response uses a generic civil-military frame and explicitly identifies operating context as an information gap. Existing `partner_types`, `civil_considerations`, and `constraints` remain supported for backward compatibility.

### Public source items

The request adds `source_items`, each containing:

- `title` (required)
- `url` (optional public URL)
- `publisher` (optional)
- `retrieved_at` (optional ISO 8601 date/time supplied by the user)
- `claim` (optional short observation from the source)
- `source_type` (optional: official, academic, NGO, news, local-government, user-provided, or other)
- `corroborated` (optional boolean)

Source items support traceability; they do not make the application fetch, verify, or endorse the claims. Items without a claim appear as evidence gaps, not as facts.

### Infrastructure inputs

The request adds broad, non-targetable `infrastructure_systems` entries. Each is limited to system category, condition/concern, known dependency, and public-source reference label. Examples include water, power, transportation, communications, health services, fuel, shelter, and waste management. Exact facility coordinates, exploitable vulnerabilities, access methods, security posture, and disruption instructions are out of scope.

### Cultural-context inputs

The request adds `cultural_context_items`, each limited to a documented context statement, source/reference label, known regional variation, and planning relevance. The feature does not infer traits about people or groups. Users must be able to record that a context item is unknown or contested.

## Response Design

### Concise planning worksheet

The response keeps the five existing G-9 sections and adds:

- `operating_context_frame`: tailored domestic-support or overseas/partner authority and coordination prompts.
- `infrastructure_dependency_assessment`: system-level considerations, public-source observations, dependencies, potential civil effects, coordination prompts, restoration/support questions, and information gaps.
- `cultural_context_assessment`: documented context, stated variation, engagement considerations, assumptions to avoid, and information gaps.
- `evidence_and_assumptions`: a row-oriented list distinguishing `reported_fact`, `analytic_inference`, `planning_assumption`, and `synthetic_exercise_content`; each row carries a source label, source date if supplied, and confidence.

The planner never states an uncorroborated or unsourced user claim as a confirmed fact. It labels the entry as a planning assumption or gap and recommends the smallest useful validation action.

### Export-ready civil estimate outline

The response adds `civil_estimate_outline`, a list of sections ready to place into an event staff product:

1. Supported event and operating context
2. Civil situation and key actors
3. Infrastructure dependencies and civil effects
4. Cultural-context considerations and variation
5. Authorities, partner coordination, and engagement considerations
6. Key judgments, assumptions, and information requirements
7. Recommended actions, owners, and decision points
8. Sources, confidence, and verification notes

The outline contains only event-scoped content generated from the request. It does not claim to be an official Annex G, civil estimate, or country study.

### Context-specific guardrails

For `domestic_support`, outputs stress confirmation of civil authorities, emergency-management structures, legal restrictions, and the civilian lead before any coordination or support action.

For `overseas_partner`, outputs stress confirmation of host-nation authorities, embassy/country-team channels, partner/NGO independence, agreements, and releasability before engagement or support action.

Both contexts remind users to use current command guidance and approved coordination channels. The application does not determine legal authority.

## Architecture and Data Flow

1. Dashboard or API client submits an expanded `G9PlanningRequest` to `POST /staff/g9-plan`.
2. Pydantic validates the selected operating context, bounded public-source item shape, and non-empty optional item text.
3. `G9Planner.build()` constructs the existing five sections plus the new context, infrastructure, cultural, evidence, and estimate-outline sections.
4. `G9PlanningResponse` returns the complete event-scoped package. The route creates no local storage record.
5. Existing security warnings remain present. Sensitive input results in a generic advisory response through the established safety layer where applicable.

No new dependencies, migrations, stores, background jobs, external fetches, or agent registrations are required.

## Error and Empty States

- A new-client submission missing operating context shows validation guidance; legacy API calls that omit it remain valid, receive generic framing, and flag operating context as an information gap. The application does not guess domestic versus overseas use.
- With no source items, the package says that no source-backed observations were supplied and produces a research/validation plan rather than factual claims.
- With no infrastructure or cultural items, the relevant section returns a minimum planning checklist and information gaps rather than a fabricated assessment.
- A source item missing optional provenance is retained but marked as needing source/date review.
- Entries that contain sensitive patterns receive the existing prototype warning and only generic planning guidance.

## Testing

Add route and service tests that verify:

- a domestic-support request returns domestic framing, infrastructure and cultural sections, evidence labels, and the civil-estimate outline;
- an overseas/partner request returns overseas framing and does not include domestic-authority language as its primary framing;
- an unsourced claim appears as an assumption or information gap, not a reported fact;
- no source, infrastructure, or cultural inputs produce explicit gaps without empty or fabricated output;
- existing minimal G-9 requests remain valid and retain existing response sections;
- sensitive input keeps existing warning behavior and does not echo sensitive details as actionable analysis.

Run the focused tests, then the full suite, type checks, and lint:

```text
uv run pytest tests/test_new_staff_routes.py -q
uv run pytest tests/ -q
uv run mypy app tests
uv run ruff check .
```

## Explicit Non-Goals

- Persistent area studies, civil profiles, or drill-to-drill analytic records.
- Automated web collection, monitoring, scraping, or source verification.
- Infrastructure vulnerability identification, targeting support, disruption analysis, or facility-level geospatial analysis.
- Demographic profiling, predictions about group behavior, or cultural generalizations presented as fact.
- Legal determinations, authority approval, or direct outreach to agencies, partners, NGOs, or host-nation organizations.

DRAFT — Verify all references against current official sources before acting.
