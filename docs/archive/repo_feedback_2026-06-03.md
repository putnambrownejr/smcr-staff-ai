# Repo Feedback

Date: 2026-06-03

## BLUF

`smcr-staff-ai` already has a stronger core than many prototype repos: the domain model is coherent, the route surface is broad, the safety posture is explicit, and there is a clear bias toward local-first workflows.

The main improvement opportunities are not "build more random features." They are:

- package the good ideas more clearly
- make reuse paths more obvious
- tighten the bridge between operator workflows and existing routes
- reduce discovery friction for both humans and connected AI tools

## What Looks Strong

- Clear domain focus.
  - The repo stays centered on awareness, readiness, and friction reduction instead of drifting into generic assistant sprawl.
- Strong app-layer coverage.
  - There are already meaningful routes for chief briefs, actions, handoffs, analysis, staff products, monitoring, planning, personnel, and local context.
- Good local-first posture.
  - Default state living outside the repo is the right choice for privacy, portability, and avoiding accidental commits of user context.
- Useful safety model.
  - The base agent layer correctly enforces UNCLASSIFIED framing, human review, and generic fallback behavior for sensitive inputs.
- Good reuse discipline on paper.
  - `docs/core_documents/capability_reuse_audit.md` makes the right distinction between commodity connector behavior and SMCR-specific logic.
- Better-than-average test footprint.
  - The repo has broad offline test coverage, which gives it a better chance of surviving incremental growth without turning into a museum of broken good intentions.

## Biggest Improvement Areas

### 1. Skill Layer Was Too Thin

Before this pass, the repo had a rich runtime surface but almost no packaged Codex-facing skills beyond `important-staff-docs`.

Impact:

- useful workflows were present but under-advertised
- AI tools had fewer opinionated entry points
- operating patterns lived mostly in code and docs, not in reusable task overlays

Recommendation:

- keep expanding the `skills/` directory as a thin operator layer over existing routes
- prefer one skill per recurring workflow family, not one skill per tiny endpoint

### 2. Discoverability Is Still Split Across Too Many Places

Right now, a new contributor has to infer the real product shape from:

- `README.md`
- `docs/README.md`
- `docs/agents_setup/AGENTS.md`
- route files
- service folders
- demo routes

None of that is wrong, but it is heavier than necessary.

Recommendation:

- create one "start here for contributors" document that links:
  - app entrypoint
  - route inventory
  - skill catalog
  - core workflows
  - high-value next build areas

### 3. The Repo Has Core Workflows But Needs More Workflow Bridges

The repo is strongest when it turns raw input into structured follow-through:

- notes -> summary -> actions
- source updates -> monitoring brief -> due-outs
- handoffs + documents + opportunities -> chief brief

That pattern is already present, but the bridges should be more explicit.

Recommendation:

- keep improving route-to-route workflow patterns rather than adding isolated features
- focus on "promote to action," "compare against existing handoff," "build brief from source updates," and similar transitions

### 4. Demo Surface Is Strong But Underleveraged

The demo tool catalog is one of the better constructs in the repo because it translates the product into a clean external-facing surface.

Recommendation:

- treat `/demo/tool-catalog` as a first-class contract
- make sure any new high-value workflow is considered from three angles:
  - local/private route
  - demo/stateless route
  - skill/operator overlay

### 5. Some Features Are Better Framed As Adapters Than New Builds

The repo already says this, and it is correct:

- do not rebuild connector auth
- do not rebuild generic research shells
- do not rebuild generic browser QA

Recommendation:

- continue treating external connectors and operator tooling as input layers
- keep the repo focused on reserve-specific normalization, trust, action promotion, and drafting logic

## Best Candidates To Add Next

### High Priority

- `source-trust-review` skill
  - Purpose: help review verified-current vs needs-review vs update-detected material and route follow-up work cleanly.
- `personal-chief-of-staff` skill
  - Purpose: combine handoffs, actions, career watch, travel/admin due-outs, and drill prep into one operator workflow.
- `connector-adapter` skill
  - Purpose: normalize external calendar/email summaries into repo-native schemas and workflows without pretending the repo owns OAuth.

### Medium Priority

- contributor quickstart doc
  - One markdown file for "where to start, what to run, what not to rebuild."
- route-to-workflow map
  - A concise table showing which endpoints combine into real-world operating flows.
- action system maturity memo
  - Clarify ownership, suspense, status, blocked state, and audit/history expectations.

### Lower Priority

- more specialist agents
  - The repo already has many agents. More agents are probably less valuable right now than better orchestration and packaging.
- frontend polish for its own sake
  - Improve dashboard behavior when it helps real workflows, not because every repo eventually catches a redesign bug.

## Recommended Build Strategy

### Path 1: Package Existing Value Better

Keep adding:

- skills
- quickstart docs
- workflow maps
- examples tied to real routes

Why:

- fast ROI
- low risk
- improves discoverability immediately

### Path 2: Deepen Workflow Continuity

Prioritize:

- source update -> brief -> action
- meeting notes -> action tracker / POAM
- handoff -> chief brief -> reminder or follow-up flow

Why:

- this compounds the strongest parts of the repo
- this is closer to real daily use than adding another isolated advisor

### Path 3: Tighten Trust And Review Signals

Prioritize:

- stronger visibility of source freshness
- clearer status propagation for monitored sources
- explicit uncertainty handling in more route responses

Why:

- this improves credibility
- this reduces the risk of polished but stale output

## Specific Practical Suggestions

- Add a `skills/README.md` link from the root `README.md` and `docs/README.md`.
- Add one contributor-facing "workflow map" doc that shows the top 5 operating flows.
- Consider exposing a route inventory summary page if the dashboard is meant to be a discovery surface.
- Keep demo routes updated whenever major private workflows are added.
- Prefer expanding action promotion and workflow adapters before adding more one-off advisory endpoints.

## Porting Guidance From Other Builds

Good things to port from adjacent builds:

- lightweight operator skills
- daily brief style overlays
- meeting-to-action patterns
- monitoring playbooks
- concise research synthesis patterns

Things not worth porting blindly:

- generic specialist profiles that do not map to this repo's workflows
- broad personal-operating prompts unrelated to reserve workflows
- extra orchestration layers that duplicate existing repo logic

## Final Take

This repo does not need a dramatic reinvention.

It needs:

- better packaging of what already works
- clearer workflow bridges
- a slightly stronger operator layer
- disciplined reuse of external capabilities

That is a good position to be in. It is much easier to improve discoverability than to invent a coherent product after the fact.
