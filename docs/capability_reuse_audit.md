# Capability Reuse Audit

Last updated: 2026-05-14

This document sets a practical build policy for `smcr-staff-ai`.

The goal is simple:

- reuse stable plugins, skills, and connectors when they already solve a generic problem well
- build thin adapters when we need to translate those capabilities into SMCR workflows
- build custom logic only when the missing part is genuinely Marine-reserve-specific

## Decision Labels

- `Reuse as-is`
  - Use an existing plugin, connector, skill, or external workflow directly.
- `Wrap with adapter`
  - Keep the external capability, but normalize its outputs into local schemas and workflows.
- `Build custom`
  - Implement in this repo because the capability is domain-specific and not well covered elsewhere.

## Core Rule

`smcr-staff-ai` should own:

- SMCR-specific orchestration
- doctrine/source trust handling
- local context and handoff behavior
- advisory drafting logic for reserve workflows
- action tracking and follow-through

`smcr-staff-ai` should not own when avoidable:

- connector auth plumbing
- commodity inbox/calendar behavior
- generic browser QA
- generic transcript pipelines
- generic research workflow shells
- generic dashboard design tooling

## Audit Matrix

| Capability Area | Current Need | Best Decision | Why |
| --- | --- | --- | --- |
| Gmail inbox access and triage | High | `Reuse as-is` + `Wrap with adapter` | Gmail plugin already handles mailbox access well. This repo should consume summarized results and turn them into Chief/Aide, admin, and action updates. |
| Google Calendar access and daily brief | High | `Reuse as-is` + `Wrap with adapter` | Calendar plugin already solves the commodity scheduling problem. This repo should map events into drill prep, readiness, and due-out workflows. |
| Outlook / Microsoft 365 email and calendar | Medium | `Reuse as-is` + `Wrap with adapter` | Same pattern as Gmail and Google Calendar. Use the connector for access and keep reserve-specific reasoning here. |
| Video transcription and media extraction | Medium | `Reuse as-is` | A separate local transcription workflow is cleaner and safer. This repo should ingest transcript artifacts, not own the media-processing stack. |
| Frontend visual QA | Medium | `Reuse as-is` | Build Web Apps and browser skills already cover rendered QA well enough. Use them during dashboard work instead of building custom QA utilities here. |
| Dashboard visual redesign workflow | Medium | `Reuse as-is` | Existing frontend-app-builder and related skills are better suited for redesign passes. Keep this repo focused on the app itself. |
| Deep research / source gathering shell | Medium | `Reuse as-is` + `Wrap with adapter` | Existing research and web tooling can gather material. This repo should store manifests, summaries, citations, hashes, and source-state decisions. |
| Public-source ingestion normalization | High | `Build custom` | MARADMIN, doctrine, billet, and reserve-specific source normalization is core product behavior. |
| Citation and source-state trust model | High | `Build custom` | Verified-current versus update-detected versus needs-review is a central trust feature for this repo. |
| Session handoff and local context storage | High | `Build custom` | This is a product-specific memory layer with local-only handling and reserve-tailored fields. |
| Chief of Staff / Aide orchestration | High | `Build custom` | This is the core SMCR workflow brain. Existing plugins do not provide this reasoning layer. |
| AdminO / S-1 readiness support | High | `Build custom` | Reserve-specific admin friction is exactly where custom logic pays off. |
| Staff drafting scaffolds | High | `Build custom` | OPORD, WARNO, FRAGO, AAR, SITREP, routing, and reserve admin packages need local schemas and guardrails. |
| Correspondence conversion | High | `Build custom` | The repo should own naval-correspondence shaping and its warning/citation behavior. |
| Drill prep, annual training, and range planning | High | `Build custom` | These are mission workflows, not commodity tool features. |
| Action promotion and follow-through | High | `Build custom` | Turning outputs into tracked work is a core workspace behavior. |
| ADOS / SMCR BIC opportunity tracking | High | `Build custom` | Matching billet/opportunity signals to MOS, rank, geography, and reserve context is repo-specific value. |
| OSINT trust weighting and counterargumenting | High | `Build custom` | The useful part is not generic scraping. It is source weighting, cautions, and reserve-relevant synthesis. |
| Org awareness and chain lookup | Medium | `Build custom` | The data model and reserve hierarchy logic are repo-specific. |
| RAG over doctrine manifests | High | `Build custom` | Local source governance, manifest handling, and advisory retrieval rules are part of the product’s differentiator. |
| Historic figures / reading mentor | Low-Medium | `Build custom` | This is content and prompting logic specific to the Marine context rather than a plugin problem. |
| Mapping / military symbology | Low-Medium | `Wrap with adapter` | Reuse existing open-source map/symbology assets if we move into planning graphics, but do not build the low-level symbology stack from scratch here. |

## Recommended Build Policy By Area

### 1. Connectors

Policy:

- do not build direct Gmail, Outlook, Google Calendar, or Graph clients first
- use existing connectors/plugins for access and consent
- keep a local adapter layer that converts connector outputs into:
  - Chief brief inputs
  - career watch inputs
  - admin readiness inputs
  - tracked actions
  - session handoff update candidates

Build here:

- connector-shaped schemas
- normalization services
- reserve-specific reasoning

Do not build here first:

- OAuth flows
- mailbox sync engines
- generic calendar CRUD layers

### 2. Research And Source Collection

Policy:

- use existing research tooling to find and summarize public material
- use this repo to decide what becomes a tracked source

Build here:

- manifests
- source hashing
- source review status
- citation formatting
- update candidates
- verified source states

Do not build here first:

- a generic deep research platform
- open-ended scraping infrastructure without strong need

### 3. Local Media

Policy:

- keep transcription and scene extraction outside this repo
- treat this repo as the consumer of transcript and notes artifacts

Build here:

- media artifact ingest
- transcript summary association
- mapping media insights into product features or training patterns

Do not build here first:

- ffmpeg pipelines
- Whisper runtime management
- large-media processing orchestration

### 4. Frontend

Policy:

- use existing UI and browser skills for redesign, testing, and QA support
- only implement changes here when they improve actual reserve workflows

Build here:

- dashboard behavior
- data contracts
- workflow-specific interactions

Do not build here first:

- custom visual QA infrastructure
- design-system tooling unless the dashboard genuinely needs it

## Immediate Next-Step Options

### Option A: Plugin-First Connector Adapters

Build:

- normalized schema layer for Gmail and Calendar summaries
- import/adapter routes for connector-fed data
- Chief/Aide consumption of those normalized inputs

Why this is the best next move:

- highest practical value
- avoids rebuilding connector plumbing
- moves the product toward actual daily use

Decision:

- `Recommended next step`

### Option B: Source-Trust Propagation

Build:

- source-state badges in more agent responses
- stronger verified-current versus needs-review output handling

Why:

- major trust improvement
- especially valuable for doctrine and admin references

Decision:

- `Second priority`

### Option C: Action System Maturity

Build:

- richer filtering
- bulk state updates
- history or audit trail
- better owner/status/suspense handling

Why:

- strengthens the workspace backbone
- compounds every other workflow

Decision:

- `Third priority`

### Option D: AdminO / S-1 Depth

Build:

- deeper DTS
- awards and routing maturity
- document validation tied to admin workflows

Why:

- very SMCR-relevant
- strong painkiller area

Decision:

- `Fourth priority`

## Working Rule For Future Builds

Before adding a new capability, ask:

1. Does a plugin, connector, or skill already solve the generic part?
2. If yes, can we adapt its outputs instead of rebuilding it?
3. Is the missing value genuinely SMCR-specific?
4. If not, do not build it here.

Short version:

- `reuse generic capability`
- `build reserve-specific judgment`

