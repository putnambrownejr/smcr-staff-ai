# Staff Operating Model

This document describes the planned operating model for `smcr-staff-ai` as a reserve staff assistant.

## Chief Of Staff / Aide de Camp

The Chief of Staff / Aide de Camp function is the user's front door for routine staff awareness.

Initial responsibilities:

- Drill weekend preparation
- General news and MARADMIN awareness
- PME/FitRep/admin watch items
- Routing questions to staff agents
- Calendar/email triage once user-approved connectors are implemented
- Local session handoff management

Current implementation:

- Agent id: `chief-of-staff-aide`
- API: `/agents/chief-of-staff-aide/run`
- Orchestration API: `/chief/brief`
- Session handoff API: `/handoffs/{user_key}`
- Connector planning API: `/connectors/chief-digest-plan`
- Calendar status: local ICS export exists; Microsoft Graph and Google Calendar are stubs.
- Email status: provider interface exists; live mailbox access is not enabled.

The orchestration brief combines session handoff data, local personal documents, stored drill plans, MARADMIN-driven documentation update candidates, and professional reading suggestions into one advisory triage object.

The connector digest planner is the next bridge step before live integration. It accepts consent state plus summarized calendar/email metadata and returns a consent-safe digest plan, suggested read scope, staged follow-up actions, and warnings without performing any external read or write.

## AdminO / S-1 Support

The AdminO / S-1 support layer is intended to reduce reserve administration drift between drills.

Current implementation:

- Agent id: `admin-readiness-advisor`
- API: `/agents/admin-readiness-advisor/run`
- Digest API: `/admin/readiness/{user_key}`

The admin readiness digest combines:

- FitRep reminders from the handoff
- admin watch items
- local orders/RQS/FitRep/DTS document gaps
- medical and dental readiness reference gaps
- travel and voucher support reminders

This is advisory continuity support only. It is not a replacement for official S-1/AdminO processes, unit systems of record, or command review.

The admin workflow builder adds focused support for:

- DTS voucher checklists
- orders review
- general admin package routing
- award package routing support

## Session Handoffs

Session handoffs persist minimum necessary local user context, such as:

- Rank, MOS, billet, and unit id
- PME status and due dates
- FitRep reminders
- Recurring drill notes
- Admin watch items
- User preferences

Do not store secrets, PII beyond minimum required, CUI, classified information, or sensitive operational details.

## Personal Document Organizer

The personal document organizer lists local user-uploaded records such as RQS, BIO, orders, travel receipts, DTS artifacts, PME certificates, readiness references, FitRep references, and drill plans.

API:

- `GET /personal-documents`

These files remain local context and do not become canonical doctrine or official records. PII warnings are surfaced so the user can decide whether the local record is necessary to retain.

The organizer also supports review and expiration dates for local records so the Chief/Aide brief can nudge the user about stale or missing personal references.

## Staff Council

The staff council lets a user run ideas through role-based advisors by echelon.

API:

- `GET /staff/roles`
- `POST /staff/vet-idea`
- `POST /staff/round-robin`

Company roles:

- XO
- 1stSgt
- Company Gunnery Sergeant

Battalion roles:

- XO
- OpsO / S-3
- SgtMaj
- S-1 through S-6

Division/group roles:

- G-1 through G-6

The roles are housed in a single implementation file with different instructions, maturity, scope, and role lenses.

The round-robin route runs staff perspectives across company, battalion, and division/group echelons by default. It returns requested roles, roles run, structured citations where available, assumptions, action items, and warnings. Unknown role names are rejected so a partial review is not mistaken for a complete staff pass.

## S-2 / G-2 And OSINT

The S-2 and G-2 roles are tied to the OSINT source-evaluation workflow. When staff council context includes `source_items`, S-2/G-2 perspectives call the OSINT agent and include citations from that public-source evidence.

Rules:

- Topic-level public trends only
- Always cite supplied source URLs
- Treat social media as noisy signal
- Do not infer sensitive operational details from public chatter
- Do not collect private personal data or bypass access controls

## Build Stages

### Stage 1: Staff OS Scaffolding

- Chief of Staff / Aide agent
- Local session handoff store
- Staff council API
- S-2/G-2 to OSINT tie-in
- Email/calendar provider interfaces

### Stage 2: Live Public Source Awareness

- MARADMIN RSS and print-view parser
- MCPEL item-page parser and PDF-link extractor
- MARFORRES hierarchy and exercise-page parsers
- News/MARADMIN digest surfaced to Chief/Aide

### Stage 3: RAG With Citations

- Allowlisted source ingestion from manifests
- Chunked doctrine/publication retrieval
- Citation-aware agent responses
- Document freshness and supersession warnings

The current source verification route is an intermediate step toward stronger freshness handling. It validates source refs, flags tag-page-only and placeholder sources, and helps identify MCPEL references that still need exact item-page verification.

### Stage 4: User-Approved Email And Calendar

- Microsoft Graph integration
- Google Calendar integration if needed
- Gmail/Outlook provider option if approved
- Token protection, least scopes, no hidden mailbox reads
- Calendar/email summaries routed to Chief/Aide

### Stage 5: Staff Maturity And Workflow Automation

- Staff estimates
- Decision logs
- Task trackers
- Drill weekend battle rhythm
- PME/FitRep/admin suspense dashboards
- Multi-agent staff review with dissent/counterarguments

### Stage 6: Frontend

- Staff dashboard
- Drill prep view
- Handoff editor
- Staff council panel
- Source/citation explorer
