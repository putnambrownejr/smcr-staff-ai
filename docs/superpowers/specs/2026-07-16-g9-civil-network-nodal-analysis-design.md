# G-9 Civil Network / Nodal Analysis Design

## Goal

Add an event-scoped, evidence-bound civil-network dataset for G-9/Civil Affairs planning. It supports fictional exercise networks and real-world, public civil-environment context without becoming a people-tracking, targeting, or vulnerability-analysis tool.

## Scope and boundaries

- One network belongs to one exercise or event. Users may deliberately copy a previous network, but no network is silently reused across events.
- Nodes represent public organizations, institutions, services, community groups, decision forums, broad population segments, and publicly sourced key leaders in a role-bound capacity.
- A named public leader requires a public role, organization, event-relevance statement, source/date, and review state. It must not store private contact details, private affiliations, home/location details, sensitive movement, or individual influence scores.
- Relationships are limited to `coordination`, `dependency`, `influence`, `information_flow`, `authority_approval`, `resource_support`, and `legitimacy_trust`.
- The feature supports only UNCLASSIFIED, public, local-training, or fictional context. It does not produce targeting, collection tasking, tactical advice, exploit paths, real-world intent prediction, or sensitive vulnerability analysis.
- Every advisory product retains: `DRAFT — Verify all references against current official sources before acting.`

## Data model

`CivilNetwork` is event-scoped and owner-scoped. It contains title, event identifier, purpose, status, timestamps, nodes, relationships, and immutable snapshots.

`CivilNetworkNode` contains a stable id, node type, display name, role (when applicable), organization, event relevance, status, tags, and evidence records. Node types distinguish organization/service/forum/broad group from public role-holder so the UI and outputs can maintain the boundary.

`CivilNetworkRelationship` connects two existing node ids. It contains one relationship type, a directional or mutual flag, a concise planning description, confidence, review state, evidence records, and notes. It may not describe targets, vulnerabilities, or private-person behavior.

`CivilNetworkEvidence` supports either:

1. a reviewed Source Library reference, retaining source id, hash, title, URL, publisher, retrieval date, trust state, and excerpt; or
2. a manual citation, requiring title/source label, date, URL or bibliographic note, claim/excerpt, confidence, and reviewer state.

Each node and relationship is classified as one of `sourced_observation`, `analytic_inference`, or `planning_hypothesis`. Inferences retain a rationale; hypotheses are visibly unverified. A relationship cannot be marked sourced observation without at least one evidence record.

## Workflow

1. The user creates an exercise/event civil network and selects fictional or real-world public context.
2. The user imports reviewed saved-source evidence and/or adds a cited manual entry.
3. The user creates and reviews nodes, then adds typed relationships with evidence, inference, or hypothesis labels.
4. The system validates scope, provenance, staleness, owner/event boundaries, node references, and prohibited content.
5. The user creates a snapshot before using the network in a planning product.
6. G-9, Area Study Builder, Actor Network Analyst, Information Requirements Manager, IPB Assistant, and Red Team consume a selected snapshot read-only.
7. Derived products render observations, inferences, hypotheses, evidence gaps, competing interpretations, and verification needs separately.

## Product integration

The Actor Network Analyst becomes the analysis and rendering layer over a selected Civil Network snapshot rather than manufacturing an unpersisted network. It may flag missing evidence, unclear relationships, and planning questions, but does not alter the saved network.

The G-9 planner uses a snapshot to populate civil situation, partner coordination, infrastructure/service dependencies, public-role engagement considerations, continuity notes, and the civil-estimate evidence/assumptions section.

Area Study, Information Requirements, IPB, and Red Team accept a snapshot reference or structured handoff. They preserve the original labels and provenance. They may create high-level questions and discriminators, but not collection tasking or operational recommendations.

## Map and usability

The first UI is a data-first event workspace: filterable node and relationship tables plus a generated map. The map is a derived view, not the source of truth. It shows relationship type, confidence, evidence status, stale-source warning, and review state. Users can inspect a node/edge to see its supporting evidence and remove or revise it.

The initial map avoids centrality scores, vulnerability rankings, and automated relationship discovery. The user creates/reviews each relationship; the assistant can only propose an explicitly labeled draft based on selected local sources.

## Validation and error handling

- Reject cross-owner, cross-event, missing-node, invalid-relationship-type, and cited-observation-without-evidence writes.
- Warn rather than silently omit stale/watch sources; only reviewed/current sources can support a sourced observation by default. An explicit user opt-in is required to include a noncurrent source and outputs retain its warning.
- Reject prohibited sensitive detail and return generic safe guidance.
- Render missing evidence as an evidence gap; never infer a relationship as fact merely because two nodes appear in the same source.
- Preserve snapshots even if the working network changes; deleted sources surface as provenance gaps in historical snapshots.

## Testing and acceptance criteria

- Event and owner isolation prevents cross-event/cross-user access.
- A public leader node cannot be saved without a role, organization, source/date, and event relevance.
- A sourced-observation relationship requires evidence; inference/hypothesis labels render distinctly.
- Source Library evidence retains source hash, URL, publisher, retrieval date, and trust state; manual citations retain required citation fields.
- Stale/watch-source behavior is warned and opt-in only.
- Snapshot-driven G-9 and specialist-agent outputs preserve provenance and separate facts, inferences, hypotheses, and gaps.
- Map data contains no prohibited targeting, private-person, or vulnerability fields.
- All outputs include the required draft footer.

## Out of scope

- Persistent cross-event baseline networks.
- Private contact management, social-media/person dossiers, or automated public-web collection.
- Automated graph scoring, social-network influence scoring, targeting, or vulnerability ranking.
- Dashboard agent execution consoles.

