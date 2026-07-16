# Source-Aware Planning Agents Design

## Goal

Add four discoverable planning and intelligence specialists, extend Red Team and
Assessment/Learning with explicit decision modes, and let those agents use
user-selected or locally retrieved Source Library evidence without making the
dashboard an agent-execution surface.

## Scope

The runtime registry will add:

- `information-requirements-manager`
- `area-study-builder`
- `actor-network-analyst`
- `ipb-assistant`

The following existing agents will be extended:

- `red-team-assumptions-challenge`: `assumptions`, `evidence`, and
  `hypotheses` modes.
- `assessment-learning-advisor`: measurable correction and next-drill
  verification workflow.

The dashboard continues to discover agents only. It will not gain a run console
or agent-execution controls in this scope.

## Shared Source Context

### Request contract

Agent and chain requests will accept an optional, typed source-selection object:

- `source_ids`: explicit saved local source IDs selected by the user.
- `query`: optional local Source Library search query.
- `limit`: bounded number of local excerpts to retrieve when `query` is set.
- `include_noncurrent`: explicit opt-in for retained sources that are not marked
  `current`.

The request's `context.user_key` is required whenever a source selection is
supplied. A missing user key, inaccessible source ID, or unknown ID is rejected
rather than silently ignored.

### Resolution and trust behavior

A shared resolver will read only the user's own local Source Library records.
It will combine explicit attachments and optional query hits, deduplicate them
by chunk identity, and place normalized evidence in `AgentContext.extra`.

No external fetch is permitted during an agent or chain run. Source Library
preview, fetch, recheck, review, and removal remain the only retrieval and
lifecycle operations.

Sources marked `current` are eligible evidence. Other trust states are excluded
by default and reported as warnings. `include_noncurrent=true` permits their
use only with explicit warning and preserves their trust state in the response.
Every resulting structured citation retains title, URL, publisher, retrieval
time, content hash, page/paragraph or chunk identity where available, and the
source trust marker.

### Applicability

The resolver is used by the four new specialists, Red Team, and
Assessment/Learning. Existing advisors do not change behavior in this effort.

## Specialist Agent Contracts

### Area Study Builder

Produces a public-source, planning-level baseline using PMESII and ASCOPE:

- operational area framing;
- population, governance, infrastructure, cultural and civil context;
- relevant organizations, events, and access constraints;
- source-backed observations, confidence, and gaps.

It does not claim current ground truth when supplied evidence is absent or
stale. Its structured output is suitable for Actor Network, IR, and IPB steps.

### Actor Network Analyst

Produces a planning-level network of organizations, institutions, and broad
actor categories:

- interests, capabilities, influence, relationships, and friction points;
- confidence and evidence basis for each relationship;
- unanswered questions and collection needs.

It explicitly excludes private-person profiling, individual targeting, and
operational inference about real-world units or movements.

### Information Requirements Manager

Turns a planning problem and prior assessments into a decision-linked register:

- PIR, FFIR, and CIR;
- decision supported, indicator, collection question, and recommended owner;
- priority, information gap, and review/validation condition.

It does not assign real collection tasks or claim authorities. It creates an
advisory staff register for human review.

### IPB Assistant

Builds a training/public-source four-step IPB scaffold:

- define the operational environment;
- describe environmental effects, including infrastructure and civil factors;
- evaluate broad threat or hazard patterns;
- identify event-template indicators, collection gaps, and decision points.

It stays generic for sensitive requests and distinguishes evidence, assumptions,
and analytical hypotheses.

## Existing Agent Extensions

### Red Team modes

`assumptions` remains the default mode and retains the existing constructive
challenge workflow.

`evidence` mode produces a claim ledger: claim, supporting evidence, refuting
evidence, source quality, confidence, and collection need.

`hypotheses` mode produces competing hypotheses: each hypothesis, supporting and
refuting indicators, discriminator, confidence, and the observation most likely
to change the assessment.

All modes can cite resolved local evidence and must label unsupported statements
as assumptions or gaps.

### Assessment/Learning extension

The agent adds a closed-loop corrective-action register:

`observation -> standard or measure -> root cause -> corrective action -> owner
-> suspense -> next-drill verification condition`.

When a performance standard, evidence, owner, or verification condition is
missing, the response must identify the gap rather than infer completion from
attendance or anecdote.

## Structured Handoffs

Each new specialist receives a strict Pydantic scenario-output model and is
registered in the existing scenario-output union. The intended reusable chain is:

`area-study-builder -> actor-network-analyst -> information-requirements-manager
-> ipb-assistant`.

Each step can still run independently. Downstream steps consume prior structured
assessments when present and declare missing upstream inputs.

## Safety and Product Constraints

- UNCLASSIFIED, public, local, training, or fictional content only.
- Human review and explicit citations remain required for every agent.
- No external retrieval during agent execution.
- No individual targeting, private-person profiling, sensitive movements,
  COMSEC, classified information, or operational inference.
- All advisory outputs retain the project-required draft warning.

## Acceptance Criteria

1. All four IDs appear in the runtime registry and dashboard discovery catalog.
2. Each specialist returns a useful local response with follow-up questions,
   structured citations/source trust, required-human-review status, and safe
   degradation for sensitive input.
3. The four-step chain validates and forwards structured handoffs.
4. Explicit source IDs and optional local query hits are owner-scoped,
   deduplicated, cited, and trust-aware.
5. Non-current sources are excluded unless explicitly opted in, with visible
   warnings in either case.
6. Red Team produces materially distinct assumptions, evidence, and hypotheses
   outputs.
7. Assessment/Learning creates a measurable action register and flags missing
   evidence or verification conditions.
8. Existing agent behavior outside the named agents remains unchanged.
