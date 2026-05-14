# Roadmap

## Phase 0: Repo Skeleton and Stubs

FastAPI app, models, seed data, placeholder agents, local tests, and safety documentation.

## Phase 1: MARADMIN + MCPEL Ingestion

Implement resilient public-source fetchers, normalized message storage, source hashing, and update jobs.

Inputs:

- `docs/deep_research/source_inventory_integration_plan.md`
- `docs/sources/source_inventory_integration_plan.md`

Initial implementation should prioritize MARADMIN RSS/print-view parsing, MCPEL item-page parsing, and fixture-backed tests.

## Phase 1B: Staff OS Scaffolding

Chief of Staff / Aide de Camp agent, session handoffs, staff council roles by echelon, and S-2/G-2 OSINT tie-in.

Current scaffold:

- `chief-of-staff-aide`
- `/handoffs/{user_key}`
- `/staff/roles`
- `/staff/vet-idea`
- Email provider stubs
- Calendar provider stubs and local ICS export

## Phase 1A: SMCR Billet Discovery

Parse official public billet source pages where possible, surface Reserve Hub links, and rank open BICs against user MOS, rank, location, and career keywords.

## Phase 2: RAG Over Public Doctrine

Add embedding backend, vector store adapter, citation packing, retrieval evaluation, and document freshness warnings.

## Phase 3: Calendar Integration With ICS Export

Expand local `.ics` generation, recurring reminders, and user-controlled task templates.

## Phase 4: Microsoft Graph Integration

Implement OAuth, minimal scopes, token protection, and calendar write-review flow.

## Phase 5: MOS-Specific Agents: CommO and CAO

Connect MOS agents to doctrine manifests, checklist templates, and refusal policies.

## Phase 6: Full Staff Buildout

Add OpsO, LogO, AirO, IntelO, Fires, AdminO, SupplyO, TrainingO, Safety/ORM, and other staff agents.

## Phase 7: Unit Pilot

Run a controlled UNCLASSIFIED pilot with example data, feedback capture, and governance review.

## Phase 8: Public GitHub Release Governance

Formalize security reporting, contributor policy, release process, and source review.

## Phase 9: Multi-Unit/Multi-Service Expansion

Generalize organizational models, source manifests, and agent registry patterns for broader reserve and joint use.
