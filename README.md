# smcr-staff-ai

`smcr-staff-ai` is an UNCLASSIFIED, open-source-ready FastAPI prototype for AI-enabled Selected Marine Corps Reserve staff workflows. It is designed for SMCR officers, staff officers, and company/battalion/regimental staff who need advisory drafting support, public-source lookup, reserve administration helpers, local context storage, and future doctrine-grounded RAG.

This project is unofficial, not endorsed by the Marine Corps or Department of Defense, and not authoritative. All outputs are advisory drafts requiring human review.

## Project Purpose

The project has a simple center of gravity:

- **build awareness**
- **hone the user's edge**
- **reduce reserve-service friction**

In plain language, `smcr-staff-ai` exists to help Marine Corps Reservists stay aware, stay sharp, and stay ahead of the friction of reserve service by turning scattered obligations, staff problems, and training demands into organized, advisory, usable outputs.

For the fuller version, see [docs/project_purpose.md](/C:/smcr-staff-ai/docs/project_purpose.md).

## Safety First

Do not submit classified information, CUI, secrets, credentials, COMSEC, keying material, real frequencies, call signs, current operational movement details, sensitive unit plans, or unnecessary PII.

The application includes basic runtime guardrails for likely sensitive inputs, but those checks are not a substitute for human judgment, OPSEC review, or official policy. The system should produce checklists, drafts, and recommendations, not orders or official guidance.

## Current Capabilities

| Capability | What it does now | Status |
| --- | --- | --- |
| Agent registry | Lists and runs staff/MOS agents with structured responses, warnings, confidence, citations, and follow-up questions. | Working local registry |
| Chief of Staff / Aide de Camp | Coordinates drill prep, MARADMIN/news awareness, session handoffs, yearly drill rhythm, and future email/calendar triage. | Working scaffold |
| Admin readiness | Pulls FitRep reminders, admin watch items, local document gaps, readiness references, and travel/admin support into an AdminO / S-1 style view. | Working local digest |
| S-1 / Admin chief advisor | Adds an explicit S-1/Admin chief perspective for reserve admin continuity, routing discipline, awards, orders, DTS, GTCC, and suspense management. | Working advisory agent |
| S-2 / intel advisor | Adds an explicit S-2 perspective for public-source estimates, information gaps, confidence-weighted staff support, and OSINT/public-source aggregation as a subordinate lane. | Working advisory agent |
| S-3 / OpsO advisor | Adds an explicit S-3/OpsO perspective for reserve operations planning, training synchronization, battle rhythm, and decision support. | Working advisory agent |
| S-4 / logistics advisor | Adds an explicit S-4/LogO perspective for reserve supportability, movement, sustainment, supply, maintenance, and logistics friction. | Working advisory agent |
| S-6 / communications advisor | Adds an explicit S-6/CommO perspective for reserve C2 support, generic PACE framing, permissions, equipment, supportability friction, and PKI/CAC user-access issues as a subordinate lane. | Working advisory agent |
| G-9 / civil-military advisor | Adds an explicit G-9 perspective for civil considerations, partner coordination, external engagement continuity, and public context framing. | Working advisory agent |
| Medical / Doc advisor | Adds a training-safe medical-support perspective for TCCC-aware planning, 9-line familiarity, CASEVAC structure, and event medical coordination. | Working advisory agent |
| AirO advisor | Adds a generic aviation-support and air-ground coordination planning perspective for training and public staff-planning contexts. | Working advisory agent |
| JAG / legal advisor | Adds issue-spotting and escalation prompts while clearly refusing to replace formal legal counsel. | Working advisory agent |
| Chaplain advisor | Adds morale, welfare, ethics, and referral-minded leader prompts without claiming to replace real chaplain or care channels. | Working advisory agent |
| PKI / CAC troubleshooting | Builds advisory troubleshooting playbooks for CAC detection, certificate, middleware, browser-auth, signing/encryption, and portal-access issues. Also exposed as an S-6 staff-support lane. | Working local support |
| Chief/Aide orchestration brief | Combines session handoff, local personal docs, drill plans, MARADMIN-driven source updates, and reading suggestions into one advisory triage brief. | Working local orchestrator |
| Text summarizer / checklist API | Turns pasted text into a local summary, due-outs, action items, checklist, and follow-up questions without storing the input. | Working local analysis |
| Staff council | Vets ideas through company, battalion, and division/group staff roles, with S-2/G-2 tied to OSINT. Includes round-robin review. | Working scaffold |
| Staff products | Builds advisory scaffolds for OPORDs, WARNOs, FRAGOs, SITREPs, AARs, naval letters, memos, and endorsements. | Working scaffold |
| Session handoffs | Stores minimum necessary local user context for PME, FitRep, annual drill dates, recurring checks, admin, drill, and preference reminders. | Working local storage |
| Installation / base practical advisor | Helps with common Marine/joint-base access, sponsorship, REAL-ID, visitor-center, and command-event coordination friction while insisting on local verification. | Working advisory agent |
| Local context storage | Lets users upload files/notes, RQS/BIO references, and drill templates as advisory local context without changing doctrine, org, exercise, agent, or canonical document structure. | Working local storage |
| Personal document organizer | Lists local RQS/BIO/orders/travel/PME-style uploads by type and flags PII/local-retention warnings. | Working local organizer |
| Personnel products | Builds advisory FitRep planning, FitRep bullet capture, award package, and routing package support with citations and review points. | Working local support |
| Correspondence conversion | Converts rough text into NAVMAC-style naval letter, memo, endorsement, routing package, point paper, or professional email scaffolds with stronger formatting notes and routing discipline cues. | Working local support |
| Career opportunity tracker | Stores ADOS and SMCR BIC opportunities locally, ranks them against a user profile, and surfaces them in the Chief/Aide brief. | Working local tracker |
| Career watch | Pulls PME gaps, FitRep reminders, career trends, recommended courses/books, missing documents, and tracked opportunities into one advisory career-maintenance view. | Working local watch |
| Drill prep planner | Turns a drill date into advisory prep tasks, can use templated local key events, persists plans locally, exports `.ics` calendar content, and can generate reminder plans from stored handoff drill dates and recurring checks. | Working local planner |
| Annual training planning | Back-plans AT admin, logistics, readiness, and coordination considerations for reserve units. | Working local planner |
| Range / RSO package support | Builds advisory range packet, role, safety-control, no-go, command-decision, and medevac/comm checklists. | Working local support |
| SMCR BIC discovery | Lists official public billet source pages, parses public billet tables/cards where available, discovers Reserve Hub links, and ranks billets against user MOS/rank/location/keywords. | Working parser/recommender with live-source caveats |
| OSINT trend aggregation | Aggregates user-supplied trusted public-source news/social trend summaries with citations, counterarguments, and confidence weighting. Also exposed as an S-2 staff-support lane. | Working source-evaluation agent |
| Vetted social ingestion | Normalizes public news/social trend records into OSINT/deep-research-ready source items without unrestricted scraping. | Working connector |
| Professional reading catalog | Tracks Commandant's Reading List sources, archive references, open-source classics, and study summaries. | Working catalog |
| Leadership / historical perspective advisor | Brings Marine leadership doctrine, professional reading, and historical perspective into PME, command-climate, and leader-development questions without pretending to be a historical figure. | Working advisory agent |
| USMC history context | Provides an easy-access Marine Corps history and heritage study reference for agent context and PME prompts. | Markdown reference |
| Org awareness | Loads example MARFORRES-style hierarchy and answers unit chain lookups. | Working example data |
| Exercise cadence | Provides typical/advisory exercise and battle rhythm examples. | Working example data |
| RSS/MARADMIN parsing | Parses local RSS XML fixtures and tags messages by staff relevance. | Working parser; live ingestion is later |
| RAG foundations | Includes document/chunk models, chunking, local embedding stub, vector-store stub, doctrine manifest validation, and citation-preserving local RAG pipeline. | Ready for expansion |
| Lightweight dashboard | Serves a browser-based local operations board for Chief brief, admin readiness, career watch, and drafting tools. | Working local UI |

## What It Does Not Do Yet

- It does not call a real LLM.
- It does not ingest live MCPEL/MARADMIN sources by default.
- It does not automatically use local uploads as authoritative doctrine.
- It does not connect to Microsoft Graph, Google Calendar, Gmail, or Outlook yet; connector routes only create consent/write-action plans.
- It does not determine billet eligibility, assignment approval, mobilization eligibility, or command decisions.
- It does not provide official guidance, legal advice, medical advice, safety approval, or personnel decisions.

## Repository Layout

```text
app/
  api/routes/          FastAPI endpoints
  core/                Settings, logging, guardrails
  db/                  SQLModel database models and session setup
  schemas/             Pydantic request/response models
  services/
    agents/            Agent interface, registry, placeholder agents
    analysis/          Local text summarization and checklist extraction
    admin/             Admin readiness digest and AdminO / S-1 support
    billets/           SMCR billet recommendation
    calendar/          Drill-prep planner and calendar provider stubs
    career/            Career-maintenance view for PME, FitRep, docs, and opportunities
    chief/             Chief/Aide orchestration and triage brief
    ingestion/         RSS, PDF, MCPEL, MARADMIN, and billet parsing helpers
    opportunities/     Local ADOS/BIC tracking and recommendation
    org_awareness/     Example hierarchy and exercise cadence services
    rag/               Chunking, embeddings, vector store, retriever stubs
    storage/           Local user-context storage
data/
  seed/                Example org, doctrine, exercise, and agent manifests
  local_context/       Ignored local upload storage
docs/                  Architecture, governance, roadmap, source notes
tests/                 Offline fixture-based tests
```

## Setup

```powershell
cd C:\smcr-staff-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
copy .env.example .env
python -m app.db.init_db
uvicorn app.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

Open the lightweight dashboard:

```text
http://127.0.0.1:8000/dashboard
```

For a cleaner local container workflow, see [docs/docker_local.md](/C:/smcr-staff-ai/docs/docker_local.md).
For one-command local startup, use [scripts/start-local.cmd](/C:/smcr-staff-ai/scripts/start-local.cmd) or [scripts/start-local.ps1](/C:/smcr-staff-ai/scripts/start-local.ps1).

For GitHub/ChatGPT-friendly orientation, also see [docs/chatgpt_repo_mode.md](/C:/smcr-staff-ai/docs/chatgpt_repo_mode.md).
For the lowest-friction GitHub-plus-local workflow, see [docs/how_to_use_with_chatgpt.md](/C:/smcr-staff-ai/docs/how_to_use_with_chatgpt.md).
For project purpose and scope, see [docs/project_purpose.md](/C:/smcr-staff-ai/docs/project_purpose.md).
For the first-pass ChatGPT-facing tool plan, see [docs/chatgpt_app_surface.md](/C:/smcr-staff-ai/docs/chatgpt_app_surface.md).
For the current in-repo bridge scaffold, see [docs/chatgpt_app_scaffold.md](/C:/smcr-staff-ai/docs/chatgpt_app_scaffold.md).
For the new local ChatGPT app server layer, see [chatgpt_app/README.md](/C:/smcr-staff-ai/chatgpt_app/README.md).
For one-command ChatGPT app startup, use [scripts/start-chatgpt-app.cmd](/C:/smcr-staff-ai/scripts/start-chatgpt-app.cmd) or [scripts/start-chatgpt-app.ps1](/C:/smcr-staff-ai/scripts/start-chatgpt-app.ps1).
For the build-vs-reuse decision matrix, see [docs/capability_reuse_audit.md](/C:/smcr-staff-ai/docs/capability_reuse_audit.md).

## Calling The API

All examples assume the server is running at `http://127.0.0.1:8000`.

### Health

Use this to check that the service is up.

```powershell
curl http://127.0.0.1:8000/health
```

Expected shape:

```json
{
  "status": "ok",
  "classification": "UNCLASSIFIED",
  "human_review": "required"
}
```

### Stateless Demo Mode

If you only want to understand the repo behavior, or want a ChatGPT-friendly surface that does not depend on local handoffs/uploads, use the demo routes:

```powershell
curl http://127.0.0.1:8000/demo/status
curl http://127.0.0.1:8000/demo/tool-catalog
curl http://127.0.0.1:8000/demo/chief/brief
curl http://127.0.0.1:8000/demo/career/watch
```

The demo routes:

- do not require prior local context
- do not depend on your stored handoffs or uploaded files
- are intended as the canonical stateless examples for repo-mode and OpenAPI readers

`/demo/tool-catalog` returns the recommended first-pass ChatGPT-facing tool surface for a future Apps/MCP integration.

### Connector Planning

Create a consent-safe Chief/Aide connector digest plan from summarized calendar and email inputs:

```powershell
curl -X POST http://127.0.0.1:8000/connectors/chief-digest-plan `
  -H "Content-Type: application/json" `
  -d "{\"user_key\":\"capt-example\",\"consents\":[{\"provider\":\"google_calendar\",\"access_mode\":\"read_only\",\"user_key\":\"capt-example\",\"enabled\":false},{\"provider\":\"gmail\",\"access_mode\":\"read_only\",\"user_key\":\"capt-example\",\"enabled\":false}],\"calendar_events\":[{\"provider\":\"google_calendar\",\"title\":\"Drill weekend muster\",\"start_at\":\"2026-06-06T08:00:00Z\",\"location\":\"NOSC New Orleans\"}],\"email_messages\":[{\"provider\":\"gmail\",\"subject\":\"DTS voucher reminder\",\"received_at\":\"2026-06-07T14:30:00Z\",\"action_hint\":\"Voucher due this week\"}]}"
```

This route:

- performs no live mailbox or calendar reads
- takes only user-provided consent state and summarized metadata
- returns read plans, action items, and staged write ideas
- keeps review-before-write guardrails intact

Adapt plugin-fed connector summaries into Chief/Aide, handoff, and action-ready local shapes:

```powershell
curl -X POST http://127.0.0.1:8000/connectors/workflow-adapter `
  -H "Content-Type: application/json" `
  -d "{\"user_key\":\"capt-example\",\"consents\":[{\"provider\":\"google_calendar\",\"access_mode\":\"read_only\",\"user_key\":\"capt-example\",\"enabled\":true},{\"provider\":\"gmail\",\"access_mode\":\"read_only\",\"user_key\":\"capt-example\",\"enabled\":true}],\"calendar_events\":[{\"provider\":\"google_calendar\",\"title\":\"Drill weekend muster\",\"start_at\":\"2026-06-06T08:00:00Z\",\"location\":\"NOSC New Orleans\",\"notes\":\"Travel the night prior.\"}],\"email_messages\":[{\"provider\":\"gmail\",\"subject\":\"DTS voucher reminder\",\"received_at\":\"2026-06-07T14:30:00Z\",\"action_hint\":\"Voucher due this week\"}]}"
```

This route:

- does not perform connector auth or live connector reads
- assumes Gmail/Calendar or similar plugins already handled access
- returns:
  - a Chief/Aide digest
  - a `handoff_draft_request` ready for `/handoffs/{user_key}/draft-update`
  - an `action_promote_request` ready for `/actions/promote`
- keeps the repo focused on reserve-specific interpretation instead of connector plumbing

### Admin Readiness

Get an AdminO / S-1 style readiness digest:

```powershell
curl http://127.0.0.1:8000/admin/readiness/capt-example
```

This view combines:

- FitRep reminders from the session handoff
- admin watch items
- missing or stale local admin-support documents
- readiness reference gaps
- travel/DTS support gaps
- source-trust markers for the admin references that should be verified before action

Build a focused admin workflow checklist:

```powershell
curl -X POST http://127.0.0.1:8000/admin/workflow `
  -H "Content-Type: application/json" `
  -d "{\"workflow_type\":\"dts_voucher\",\"title\":\"Post-drill voucher\",\"facts\":[\"Receipts are complete\"]}"
```

Supported admin workflow types:

- `dts_authorization`
- `dts_voucher`
- `gtcc`
- `orders_review`
- `admin_package`
- `award_package`

Run the S-1 / Admin chief advisor:

```powershell
curl -X POST http://127.0.0.1:8000/agents/s1-admin-chief/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Help me organize awards, DTS, and FitRep due-outs for next drill.\",\"context\":{\"user_role\":\"S-1\"}}"
```

Use the S-1 staff wrappers for travel-admin support:

```powershell
curl -X POST http://127.0.0.1:8000/staff/s1/dts-helper `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Next drill authorization\",\"facts\":[\"Travel will start Friday night\"],\"constraints\":[\"Need approval before the end of the week\"]}"

curl -X POST http://127.0.0.1:8000/staff/s1/gtcc-helper `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Travel card reconciliation follow-up\",\"facts\":[\"Voucher is pending\"],\"constraints\":[\"Avoid delinquency risk before next drill\"]}"
```

These keep DTS and GTCC support under the S-1/Admin-chief lane instead of treating them as stand-alone functions.

### Action Tracking

Filter tracked actions:

```powershell
curl "http://127.0.0.1:8000/actions?user_key=capt-example&owner=Capt%20Example&priority=high"
```

Bulk-update tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/bulk-update `
  -H "Content-Type: application/json" `
  -d "{\"action_ids\":[\"action-a\",\"action-b\"],\"status\":\"waiting\",\"notes\":\"Awaiting review.\"}"
```

Build a PKI / CAC troubleshooting playbook:

```powershell
curl -X POST http://127.0.0.1:8000/admin/pki-troubleshooting `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"MarineNet CAC login issue\",\"issue_type\":\"browser_auth_issue\",\"symptoms\":[\"Certificate prompt never appears\"],\"browser\":\"Chrome\",\"affected_systems\":[\"MarineNet\"],\"on_government_furnished_equipment\":false}"
```

This route returns likely causes, immediate checks, deeper checks, escalation steps, and safe data-handling notes. It stays advisory and does not attempt enterprise IT actions on your behalf.

If you want the same capability surfaced in staff taxonomy, use the S-6 wrapper:

```powershell
curl -X POST http://127.0.0.1:8000/staff/s6/pki-troubleshooting `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"MarineNet CAC login issue\",\"issue_type\":\"browser_auth_issue\",\"symptoms\":[\"Certificate prompt never appears\"],\"browser\":\"Chrome\",\"affected_systems\":[\"MarineNet\"],\"on_government_furnished_equipment\":false}"
```

### Personnel Products

Build a more detailed FitRep, awards, or routing support package:

```powershell
curl -X POST http://127.0.0.1:8000/personnel/products `
  -H "Content-Type: application/json" `
  -d "{\"product_type\":\"fitrep_planning\",\"title\":\"Annual FitRep prep\",\"subject_name\":\"Capt Example\",\"occasion\":\"Annual\",\"facts\":[\"Served as battalion CommO during AT planning cycle\"],\"achievements\":[\"Built a reserve communications tracker\"]}"
```

Supported personnel product types:

- `fitrep_planning`
- `fitrep_bullets`
- `award_package`
- `routing_package`

This route returns:

- structured planning sections
- routing steps
- required documents
- review points
- citations and warnings

Convert rough text into a correspondence scaffold:

```powershell
curl -X POST http://127.0.0.1:8000/personnel/convert-correspondence `
  -H "Content-Type: application/json" `
  -d "{\"format_type\":\"naval_letter\",\"title\":\"Travel support request\",\"purpose\":\"Request travel support for reserve drill attendance.\",\"audience\":\"Battalion S-1\",\"source_text\":\"Need a short formal request asking for travel support for next month's drill.\",\"references\":[\"Orders\"],\"enclosures\":[\"Orders\",\"Travel estimate\"]}"
```

Supported correspondence formats:

- `naval_letter`
- `memorandum`
- `endorsement`
- `routing_package`
- `point_paper`
- `professional_email`

### Training And ORM

Build a training scenario scaffold:

```powershell
curl -X POST http://127.0.0.1:8000/training/scenario `
  -H "Content-Type: application/json" `
  -d "{\"scenario_type\":\"staff_drill\",\"title\":\"Battalion planning drill\",\"training_objective\":\"Practice decision-making and product flow.\",\"constraints\":[\"Three-hour window\"]}"
```

Build an S-3 / OpsO planning support draft:

```powershell
curl -X POST http://127.0.0.1:8000/training/s3-plan `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Battalion drill planning sync\",\"mission_or_training_goal\":\"Align staff outputs and support requirements for next drill weekend.\",\"event_type\":\"drill_weekend\",\"constraints\":[\"Limited Saturday planning window\"],\"coordinating_sections\":[\"S-1\",\"S-4\",\"S-6\"]}"
```

Run the S-3 / OpsO advisor:

```powershell
curl -X POST http://127.0.0.1:8000/agents/s3-opso/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Help me shape a drill weekend synchronization plan.\",\"context\":{\"user_role\":\"S-3\"}}"
```

Build an S-4 / logistics planning support draft:

```powershell
curl -X POST http://127.0.0.1:8000/training/s4-plan `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"AT logistics sync\",\"supported_event\":\"Annual training movement\",\"support_objective\":\"Support distributed personnel arrival and sustainment.\",\"travel_required\":true,\"overnight\":true,\"support_requirements\":[\"Billeting\",\"Chow\",\"Equipment issue\"]}"
```

Run the S-4 / logistics advisor:

```powershell
curl -X POST http://127.0.0.1:8000/agents/s4-logistics/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Help me think through supportability for an AT movement plan.\",\"context\":{\"user_role\":\"S-4\"}}"
```

### Staff Estimates And Support Plans

Build a general staff-planning package:

```powershell
curl -X POST http://127.0.0.1:8000/planning/staff-package `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Reserve field training package\",\"event_type\":\"field_training\",\"mission_or_training_goal\":\"Build a one-day field event that improves staff and small-unit readiness.\",\"audience\":\"Civil affairs company\",\"timeframe\":\"Next drill weekend\",\"constraints\":[\"One field day\",\"Distributed Marines\",\"Travel required\"],\"coordinating_sections\":[\"S-1\",\"S-4\",\"S-6\",\"Safety / ORM\"],\"support_requirements\":[\"Billeting\",\"Movement accountability\",\"Medical support\"],\"product_types\":[\"warno\",\"frago\",\"aar\"],\"training_only\":true}"
```

This route is the current best single-entry planning workflow. It:

- builds cross-staff estimates
- synthesizes a recommended course of action
- surfaces commander decisions, top risks, cuts, and execution framework
- runs battalion staff review and XO vet
- optionally pulls in G-9 when the problem is civil-military relevant
- returns a product package ready for follow-on drafting and action promotion

Build an S-2 public-source estimate:

```powershell
curl -X POST http://127.0.0.1:8000/staff/s2-estimate `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Exercise sentiment estimate\",\"question\":\"What does public reporting suggest about upcoming exercise sentiment?\",\"source_items\":[{\"title\":\"Official release\",\"source_type\":\"official\",\"claim\":\"The event is proceeding as planned.\",\"corroborated\":\"true\"}]}"
```

Run the S-2 advisor:

```powershell
curl -X POST http://127.0.0.1:8000/agents/s2-intel/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Help me shape a public-source estimate for a staff question.\",\"context\":{\"user_role\":\"S-2\"}}"
```

Run the S-2 OSINT wrapper when you already have trusted public source items to aggregate:

```powershell
curl -X POST http://127.0.0.1:8000/staff/s2/osint-estimate `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Build an OSINT-style public-source estimate for the commander.\",\"context\":{\"source_items\":[{\"title\":\"Official release\",\"publisher\":\"Example official source\",\"source_type\":\"official\",\"url\":\"https://example.test/official\",\"claim\":\"Training event details were publicly announced.\",\"corroborated\":\"true\"}]}}"
```

This keeps OSINT as a specialist public-source lane under the S-2 surface instead of a separate free-floating function.

Build an S-6 communications support draft:

```powershell
curl -X POST http://127.0.0.1:8000/staff/s6-plan `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Drill comm sync\",\"supported_event\":\"Drill weekend planning event\",\"c2_objective\":\"Support leader coordination and accountability.\",\"support_requirements\":[\"Equipment issue\",\"Battery plan\"]}"
```

Run the S-6 advisor:

```powershell
curl -X POST http://127.0.0.1:8000/agents/s6-comms/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Help me shape generic comm support for next drill.\",\"context\":{\"user_role\":\"S-6\"}}"
```

This S-6 lane now also owns PKI/CAC troubleshooting at the staff surface, while still keeping the specialist troubleshooting workflow available on its own route.

Build a G-9 civil-military planning support draft:

```powershell
curl -X POST http://127.0.0.1:8000/staff/g9-plan `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Community coordination support\",\"supported_problem\":\"Prepare for a training event with local community touchpoints and external coordination.\",\"partner_types\":[\"Local authorities\",\"Community partners\"],\"civil_considerations\":[\"Limited local familiarity between drills\"],\"constraints\":[\"Keep everything public-source and advisory\"]}"
```

Run the G-9 advisor:

```powershell
curl -X POST http://127.0.0.1:8000/agents/g9-civil-military/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Help me think through external coordination and continuity for a reserve-supported event.\",\"context\":{\"user_role\":\"G-9\"}}"
```

In staff round robins, G-9 is treated as a division/group-level lane and is only pulled into general-staff passes when the question is civil-military or partner-coordination relevant, unless you explicitly request it.

Build a medical-support planning draft:

```powershell
curl -X POST http://127.0.0.1:8000/staff/medical-plan `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Field training med plan\",\"supported_event\":\"One-day field event\",\"medical_risk_context\":[\"Heat injury risk\",\"Distributed personnel\"],\"casualty_scenarios\":[\"Vehicle rollover\",\"Heat casualty\"],\"travel_required\":true}"
```

Run the Doc advisor:

```powershell
curl -X POST http://127.0.0.1:8000/agents/medical-doc-advisor/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Help me think through a training-safe CASEVAC and TCCC support plan.\",\"context\":{\"user_role\":\"Doc\"}}"
```

Build a range/RSO support checklist:

```powershell
curl -X POST http://127.0.0.1:8000/training/range-safety `
  -H "Content-Type: application/json" `
  -d "{\"event_name\":\"Annual rifle range\",\"weapon_systems\":[\"M4\"],\"ammunition\":[\"5.56 ball\"]}"
```

Build an annual training planning scaffold:

```powershell
curl -X POST http://127.0.0.1:8000/training/annual-training-plan `
  -H "Content-Type: application/json" `
  -d "{\"unit_name\":\"Example Company\",\"training_objectives\":[\"Complete AT readiness lane\",\"Run staff battle drill\"],\"date_window\":\"FY26 Q3\",\"travel_required\":true,\"distributed_personnel\":true}"
```

Build a fuller range package:

```powershell
curl -X POST http://127.0.0.1:8000/training/range-package `
  -H "Content-Type: application/json" `
  -d "{\"event_name\":\"Annual rifle range\",\"unit_name\":\"Example Company\",\"weapon_systems\":[\"M4\"],\"ammunition\":[\"5.56 ball\"],\"travel_required\":true}"
```

### Source Verification

Verify source freshness and public-prototype eligibility:

```powershell
curl -X POST http://127.0.0.1:8000/documents/verify-sources `
  -H "Content-Type: application/json" `
  -d "{\"manifest_path\":\"data/seed/doctrine_manifest.example.yaml\"}"
```

This verification route highlights:

- placeholder or tag-page-only source refs
- public-prototype eligibility issues
- MCPEL refs that still need exact item-page verification

### Agents

List available agents:

```powershell
curl http://127.0.0.1:8000/agents
```

Run an agent:

```powershell
curl -X POST http://127.0.0.1:8000/agents/mos-commo/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Build a training-only PACE checklist for a drill weekend\",\"context\":{\"request_is_training_or_fictional\":true}}"
```

Run the OSINT trend aggregator with trusted public source items:

```powershell
curl -X POST http://127.0.0.1:8000/agents/osint-research-assistant/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Summarize public discussion of a reserve training topic\",\"context\":{\"extra\":{\"source_items\":[{\"title\":\"Official release\",\"publisher\":\"Example official source\",\"source_type\":\"official\",\"url\":\"https://example.test/official\",\"claim\":\"A public training date changed\",\"corroborated\":\"true\"},{\"title\":\"Local reporting\",\"publisher\":\"Example news\",\"source_type\":\"news\",\"url\":\"https://example.test/news\",\"summary\":\"Local reporting repeats the same date change\",\"counterargument\":\"The reporting may not apply to every unit\"}]}}}"
```

Agent responses use this shape:

```json
{
  "agent_id": "mos-commo",
  "answer": "Planning draft text...",
  "citations": [],
  "structured_citations": [],
  "warnings": ["UNCLASSIFIED prototype..."],
  "human_review_required": true,
  "confidence": "low",
  "follow_up_questions": ["Is the scenario fictional/training-only?"]
}
```

The local dashboard uses these same backend routes and can be a friendlier way to exercise the system when you do not want to hand-build payloads.

The OSINT agent is intentionally source-evaluation oriented. It does not bypass access controls or scrape social platforms directly. Pass already-collected public source summaries/URLs in `context.extra.source_items`; the agent will cite them, identify counterarguments, and mark truth confidence as high/medium/low/unknown style language in the answer.

### Local Text Analysis

Analyze pasted notes without storing them:

```powershell
curl -X POST http://127.0.0.1:8000/analysis/summarize `
  -H "Content-Type: application/json" `
  -d "{\"focus\":\"drill weekend prep\",\"text\":\"Planning notes for drill. Confirm muster timeline with the company office. DTS voucher due NLT 06/10/2026. Prepare uniform and pack field gear. Need to review the training lane sequence before Friday.\"}"
```

The response includes:

- `summary_points`
- `action_items`
- `due_outs`
- `checklist`
- `follow_up_questions`
- `warnings`

This route is local-only and does not store the submitted text. If the text looks operationally sensitive or includes likely PII, the service falls back to generic handling guidance instead of echoing details back.

### Action Promotion

Promote generated due-outs or checklist items into tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/promote `
  -H "Content-Type: application/json" `
  -d "{\"user_key\":\"capt-example\",\"default_owner\":\"Capt Example\",\"source_ref\":\"Drill notes\",\"items\":[{\"text\":\"DTS voucher due 06/10/2026 after drill.\"},{\"text\":\"Review FitRep support form this week.\"}]}"
```

This route:

- infers category, priority, and suspense date when obvious
- preserves a shared source reference across promoted items
- can attach shared or per-item links to local context, documentation updates, or URLs
- gives you real tracked actions instead of leaving due-outs buried in summaries

Promote a Chief brief straight into tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/from-chief-brief `
  -H "Content-Type: application/json" `
  -d "{\"user_key\":\"capt-example\"}"
```

Promote admin readiness items into tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/from-admin-readiness/capt-example `
  -H "Content-Type: application/json" `
  -d "{}"
```

Promote an annual training plan into tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/from-annual-training-plan `
  -H "Content-Type: application/json" `
  -d "{\"plan\":{\"unit_name\":\"Example Company\",\"training_objectives\":[\"Run AT battle drill\"],\"travel_required\":true},\"options\":{\"user_key\":\"capt-example\",\"owner\":\"Capt Example\"}}"
```

Promote a correspondence conversion into tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/from-correspondence-conversion `
  -H "Content-Type: application/json" `
  -d "{\"draft\":{\"format_type\":\"naval_letter\",\"title\":\"Travel support request\",\"purpose\":\"Request travel support for drill attendance.\",\"source_text\":\"Need a short formal request for drill travel support.\"},\"options\":{\"user_key\":\"capt-example\",\"owner\":\"Capt Example\"}}"
```

Promote a range package into tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/from-range-package `
  -H "Content-Type: application/json" `
  -d "{\"package\":{\"event_name\":\"Annual rifle range\",\"weapon_systems\":[\"M4\"],\"ammunition\":[\"5.56 ball\"],\"travel_required\":true},\"options\":{\"user_key\":\"capt-example\",\"owner\":\"Capt Example\"}}"
```

Apply follow-up notes to tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/follow-up `
  -H "Content-Type: application/json" `
  -d "{\"action_ids\":[\"abc123\"],\"notes\":\"Completed after final review.\"}"
```

If you do not set `status`, the system infers one from note language such as `completed`, `blocked`, `waiting`, or `in progress`.

Promote a TDG into tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/from-tdg `
  -H "Content-Type: application/json" `
  -d "{\"tdg\":{\"title\":\"Reserve convoy link-up\",\"theme\":\"small-unit decision-making under time pressure\",\"training_objective\":\"Practice tactical judgment.\"},\"options\":{\"user_key\":\"capt-example\",\"owner\":\"Capt Example\"}}"
```

Promote a POA&M scaffold into tracked actions:

```powershell
curl -X POST http://127.0.0.1:8000/actions/from-poam `
  -H "Content-Type: application/json" `
  -d "{\"poam\":{\"title\":\"Drill support order POA&M\",\"higher_guidance\":[\"Establish reporting timeline for drill weekend support.\",\"Coordinate S-6 comm checks and S-4 logistics support.\"],\"staff_sections\":[\"S-3\",\"S-4\",\"S-6\"]},\"options\":{\"user_key\":\"capt-example\"}}"
```

### Vetted Social / News Trend Ingestion

List allowed source categories:

```powershell
curl http://127.0.0.1:8000/social/sources
```

Normalize public trend records for OSINT or deep-research use:

```powershell
curl -X POST http://127.0.0.1:8000/social/ingest `
  -H "Content-Type: application/json" `
  -d "{\"topic\":\"Reserve recruiting public discussion\",\"records\":[{\"title\":\"Official post\",\"url\":\"https://example.test/official-post\",\"publisher\":\"Example official source\",\"source_type\":\"official\",\"summary\":\"Official public update about a recruiting event.\",\"claim\":\"A public recruiting event was announced.\",\"corroborated\":true},{\"title\":\"Public trend summary\",\"url\":\"https://example.test/social-trend\",\"publisher\":\"Example platform export\",\"source_type\":\"social_trend\",\"platform\":\"example-social\",\"summary\":\"Topic-level public discussion increased around the event.\",\"trend_signal\":\"Increased public mentions of the recruiting event.\",\"counterargument\":\"Platform discussion may reflect amplification rather than broad public interest.\"}]}"
```

The response includes `osint_source_items`. Pass that array into `/agents/osint-research-assistant/run` as `context.extra.source_items`. This is the intended bridge for later deep-research workflows.

Initial agents:

- `admin-readiness-advisor`
- `chief-of-staff-aide`
- `maradmin-monitor`
- `uniform-advisor`
- `drill-prep-calendar`
- `doctrine-opord-assistant`
- `staff-products`
- `training-planner`
- `orm-risk-management`
- `fitrep-assistant`
- `leadership-advisor`
- `osint-research-assistant`
- `mos-commo`
- `mos-civil-affairs`

Staff council agents are also registered as `staff-{echelon}-{role}`, such as `staff-company-xo`, `staff-battalion-s2`, and `staff-division_group-g2`.

### Chief Of Staff / Aide de Camp

Run the Chief/Aide agent:

```powershell
curl -X POST http://127.0.0.1:8000/agents/chief-of-staff-aide/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Build my weekly staff triage\",\"context\":{\"extra\":{\"handoff\":{\"pme\":[\"EWSDEP incomplete\"],\"fitreps\":[\"Annual FitRep due in June\"],\"admin_watch_items\":[\"DTS voucher after drill\"]}}}}"
```

Store a local session handoff:

```powershell
curl -X PUT http://127.0.0.1:8000/handoffs/capt-example `
  -H "Content-Type: application/json" `
  -d "{\"user_key\":\"capt-example\",\"rank\":\"Capt\",\"mos\":\"0602\",\"billet\":\"CommO\",\"pme\":[{\"program\":\"EWSDEP\",\"status\":\"incomplete\",\"due_date\":\"2026-09-30\"}],\"fitreps\":[{\"occasion\":\"Annual\",\"due_date\":\"2026-06-30\",\"role\":\"MRO\"}],\"admin_watch_items\":[\"DTS voucher after drill\"]}"
```

Session handoffs can reference RQS/BIO uploads by `rqs_context_id` and `bio_context_id`, but those uploads remain local context records. They do not automatically update a profile or become authoritative facts without later user confirmation logic.

Draft a proposed handoff update from notes:

```powershell
curl -X POST http://127.0.0.1:8000/handoffs/capt-example/draft-update `
  -H "Content-Type: application/json" `
  -d "{\"notes\":\"- PME: EWSDEP incomplete due 2026-06-30\n- FitRep Annual for MRO due 06/15/2026\n- DTS voucher after drill\n- Every drill confirm uniform and haircut\n- MarineNet course: writing refresher\"}"
```

Apply a confirmed draft patch:

```powershell
curl -X POST http://127.0.0.1:8000/handoffs/capt-example/apply-update `
  -H "Content-Type: application/json" `
  -d "{\"patch\":{\"pme\":[{\"program\":\"EWSDEP\",\"status\":\"incomplete\",\"due_date\":\"2026-06-30\"}],\"admin_watch_items\":[\"DTS voucher after drill\"]}}"
```

This two-step flow is intentional. The prototype can propose structured updates from notes, but it should not silently mutate a stored user profile.

Build an advisory Chief/Aide triage brief:

```powershell
curl -X POST http://127.0.0.1:8000/chief/brief `
  -H "Content-Type: application/json" `
  -d "{\"user_key\":\"capt-example\",\"maradmin_records\":[{\"source_id\":\"maradmin-123-26\",\"title\":\"MARADMIN 123/26 Revision of MCO 1610.7 Performance Evaluation System\",\"canonical_url\":\"https://example.test/maradmin\",\"summary\":\"This message announces an update to FitRep/PES policy published on MCPEL.\"}]}"
```

The response combines local handoff data, local personal document summaries, stored drill plans, source-update candidates, reading suggestions, and action items.

Fetch the current brief for a stored user key:

```powershell
curl http://127.0.0.1:8000/chief/brief/capt-example
```

Chief/Aide action items are sorted by priority and due date. The brief also warns when a session handoff looks stale or when core personal references such as `RQS`, `BIO`, `orders`, or PME references are missing.

Tracked ADOS and SMCR BIC opportunities also appear in the brief as career-oriented action items when stored locally.

The brief now also includes:

- `summary_lines` for a quick digest
- `top_priority_items` for the short list
- `recommended_courses` pulled from the handoff and PME follow-ups

### Staff Council

List staff roles:

```powershell
curl http://127.0.0.1:8000/staff/roles
```

Vet an idea through battalion S-2 and S-3:

```powershell
curl -X POST http://127.0.0.1:8000/staff/vet-idea `
  -H "Content-Type: application/json" `
  -d "{\"question\":\"Should we adjust public affairs posture around a training event?\",\"echelon\":\"battalion\",\"roles\":[\"s2\",\"s3\"],\"context\":{\"source_items\":[{\"title\":\"Official release\",\"publisher\":\"Example official source\",\"source_type\":\"official\",\"url\":\"https://example.test/official\",\"claim\":\"Training event details were publicly announced\",\"corroborated\":\"true\"}]}}"
```

The S-2 and G-2 roles call the OSINT source-evaluation workflow when `source_items` are present.

### Staff Products

Draft a staff product scaffold:

```powershell
curl -X POST http://127.0.0.1:8000/staff-products/draft `
  -H "Content-Type: application/json" `
  -d "{\"product_type\":\"opord\",\"topic\":\"Training-only drill weekend field exercise\",\"audience\":\"Company staff\",\"facts\":[\"Timeline is tentative\"],\"training_or_fictional\":true}"
```

Supported `product_type` values:

- `opord`
- `warno`
- `frago`
- `sitrep`
- `aar`
- `naval_letter`
- `memorandum`
- `endorsement`

This route produces section prompts and review checklists. It does not produce official orders or approved correspondence.

Run a full staff round robin across company, battalion, and division/group lenses:

```powershell
curl -X POST http://127.0.0.1:8000/staff/round-robin `
  -H "Content-Type: application/json" `
  -d "{\"question\":\"Should we change the drill weekend admin battle rhythm?\"}"
```

Unknown role names return a validation error instead of silently producing an incomplete review.

### Local Context Uploads

Local context is for user-provided working notes and files. It is stored under `data/local_context`, which is ignored by git. It does not modify doctrine manifests, org hierarchy, exercise cadence, agent registry metadata, or canonical document structure.

Upload context:

```powershell
curl -X POST http://127.0.0.1:8000/context/upload `
  -F "file=@notes.txt" `
  -F "tags=drill,local" `
  -F "document_type=other" `
  -F "consent_ack=true" `
  -F "review_date=2026-06-01" `
  -F "expiration_date=2026-12-01"
```

For RQS/BIO references, use `document_type=rqs` or `document_type=bio`. The prototype stores the file locally, marks whether likely PII was detected, and redacts basic PII from previews. It does not parse those records into permanent profile facts yet.

List uploaded context:

```powershell
curl http://127.0.0.1:8000/context
```

List organized personal documents:

```powershell
curl http://127.0.0.1:8000/personal-documents
```

Filter by document type:

```powershell
curl "http://127.0.0.1:8000/personal-documents?document_type=bio"
```

Get a single personal document with safe preview:

```powershell
curl http://127.0.0.1:8000/personal-documents/{context_id}
```

The organizer now highlights missing core document types such as `RQS`, `BIO`, `orders`, and `PME certificates`, along with review-due and expired records.

### Career Opportunities

Track ADOS or SMCR BIC opportunities locally:

```powershell
curl -X POST http://127.0.0.1:8000/opportunities/track `
  -H "Content-Type: application/json" `
  -d "{\"opportunities\":[{\"title\":\"ADOS Planner\",\"opportunity_type\":\"ados\",\"unit\":\"4th MLG\",\"location\":\"New Orleans, LA\",\"mos\":\"0502\",\"rank\":\"Capt\",\"source_url\":\"https://example.test/ados\",\"description\":\"Temporary planning support billet.\",\"due_date\":\"2026-06-15\"}]}"
```

List tracked opportunities:

```powershell
curl http://127.0.0.1:8000/opportunities
```

Filter by type:

```powershell
curl "http://127.0.0.1:8000/opportunities?opportunity_type=smcr_bic"
```

Rank manual opportunities against a user profile:

```powershell
curl -X POST http://127.0.0.1:8000/opportunities/recommend `
  -H "Content-Type: application/json" `
  -d "{\"profile\":{\"rank\":\"Capt\",\"mos\":\"0602\",\"preferred_locations\":[\"New Orleans, LA\"],\"keywords\":[\"communications\",\"plans\"]},\"opportunities\":[{\"title\":\"Communications Officer\",\"opportunity_type\":\"smcr_bic\",\"unit\":\"6th Comm Bn\",\"location\":\"New Orleans, LA\",\"mos\":\"0602\",\"rank\":\"Capt\",\"source_url\":\"https://example.test/bic\"},{\"title\":\"ADOS Planner\",\"opportunity_type\":\"ados\",\"unit\":\"4th MLG\",\"location\":\"Remote\",\"mos\":\"0502\",\"rank\":\"Capt\",\"source_url\":\"https://example.test/ados\"}]}"
```

The opportunity tracker is advisory only. It does not determine eligibility, orders, selection, or command approval.

### Career Watch

Get a consolidated career-maintenance view:

```powershell
curl http://127.0.0.1:8000/career/watch/capt-example
```

The response pulls together:

- PME gaps and due dates
- FitRep reminders
- tracked ADOS and SMCR BIC opportunities
- missing or stale career-supporting local documents
- recommended books
- recommended courses
- stored career trends from the session handoff

This view is advisory only. It helps the user stay organized and spot gaps, but it does not determine eligibility, command decisions, or official readiness status.

Read a preview:

```powershell
curl http://127.0.0.1:8000/context/{context_id}
```

Delete context:

```powershell
curl -X DELETE http://127.0.0.1:8000/context/{context_id}
```

Context metadata includes:

```json
{
  "context_id": "abc123",
  "filename": "notes.txt",
  "content_type": "text/plain",
  "size_bytes": 123,
  "sha256": "hash",
  "tags": ["drill", "local"],
  "document_type": "other",
  "contains_pii": false,
  "retention_policy": "user_managed_local",
  "advisory_only": true,
  "affects_canonical_structure": false
}
```

### SMCR BIC / Billet Recommendations

List official public source pages the app knows about:

```powershell
curl http://127.0.0.1:8000/billets/sources
```

Recommend billets for a user profile:

```powershell
curl -X POST http://127.0.0.1:8000/billets/recommend `
  -H "Content-Type: application/json" `
  -d "{\"profile\":{\"mos\":\"0602\",\"rank\":\"Capt\",\"desired_locations\":[\"Texas\"],\"keywords\":[\"communications\"],\"willing_to_travel\":true},\"max_results\":10}"
```

Request fields:

- `mos`: current or desired MOS, such as `0602` or `0530`.
- `rank`: current rank/grade, such as `Capt`, `O3`, or `Maj`.
- `desired_locations`: city/state/location strings to match against billet location text.
- `keywords`: career or staff terms such as `communications`, `civil affairs`, `training`, or `operations`.
- `source_key`: optional official source selector. Allowed values are `marforres_billets` and `manpower_dap`.
- `max_results`: number of recommendations to return.

Response fields:

- `source`: the page queried.
- `discovered_links`: Reserve Hub or billet-related links found on the page.
- `billets_seen`: number of parseable billets found.
- `recommendations`: scored matches with reasons and warnings.
- `warnings`: human-review and official-verification warnings.

Important: live billet data may be served through Reserve Hub, may require browser interaction, and can change quickly. Recommendations are relevance sorting only; they do not determine eligibility, assignment, or approval.

### Drill Prep Calendar

Create a drill-prep plan:

```powershell
curl -X POST http://127.0.0.1:8000/calendar/drill-prep-plan `
  -H "Content-Type: application/json" `
  -d "{\"drill_date\":\"2026-06-06\",\"unit_id\":\"example-1-25\",\"include_travel_tasks\":true}"
```

Use uploaded templated drill details:

```powershell
curl -X POST http://127.0.0.1:8000/calendar/drill-prep-plan `
  -H "Content-Type: application/json" `
  -d "{\"drill_date\":\"2026-06-06\",\"context_ids\":[\"abc123def4567890\"],\"key_events\":[{\"title\":\"Formation\",\"event_date\":\"2026-06-06\",\"start_time\":\"07:30:00\",\"location\":\"Reserve Center\",\"due_outs\":[\"Accountability roster\"]}]}"
```

The simple extractor looks for lines such as `Event: Check-in | Date: 2026-06-05 | Time: 18:00 | Location: Reserve Center | Uniform: Service Alphas | Due: orders, CAC`. Extracted details are marked low confidence and preserve `source_context_id`.

Export the plan as `.ics`:

```powershell
curl http://127.0.0.1:8000/calendar/drill-prep-plan/{plan_id}/ics
```

Generated tasks include typical/advisory reminders for uniform prep, haircut, gear packing, orders, DTS authorization/voucher, travel, readiness checks, PME, and training reminders.

### Organization Awareness

List example units:

```powershell
curl http://127.0.0.1:8000/org/units
```

Get chain to root:

```powershell
curl http://127.0.0.1:8000/org/units/example-supported-company/chain
```

The included hierarchy is placeholder example data only.

### Exercises

List typical/advisory exercise cadence entries:

```powershell
curl http://127.0.0.1:8000/exercises
```

Entries include ITX, WTI, annual training, battalion FEX, rifle range, PFT/CFT cycles, FitRep windows, fiscal-year planning, drill weekend prep, and DTS/travel voucher prep.

### Documents And Ingestion Stubs

List current document placeholders:

```powershell
curl http://127.0.0.1:8000/documents
```

Submit a dry-run ingestion request:

```powershell
curl -X POST http://127.0.0.1:8000/documents/ingest `
  -H "Content-Type: application/json" `
  -d "{\"source_type\":\"manifest\",\"local_path\":\"data/seed/doctrine_manifest.example.yaml\",\"dry_run\":true}"
```

This is a validation/stub path for now. Future ingestion should preserve source metadata, hashes, effective dates, classification labels, CUI flags, and chunk metadata.

The preferred source strategy is metadata/link/synopsis first. The repo should keep manifests, source notes, and summaries in markdown for quick reference, while large PDFs/PPTX and user-provided documents stay local or are fetched from official locations at runtime. This keeps the public repo lighter and reduces copyright, classification, and stale-document risk.

Check for documentation update candidates from MARADMIN-style records:

```powershell
curl -X POST http://127.0.0.1:8000/documents/check-updates `
  -H "Content-Type: application/json" `
  -d "[{\"source_id\":\"maradmin-123-26\",\"title\":\"MARADMIN 123/26 Revision of MCO 1610.7 Performance Evaluation System\",\"canonical_url\":\"https://example.test/maradmin-123-26\",\"summary\":\"This message announces an update to FitRep/PES policy published on MCPEL.\"}]"
```

List persisted update candidates:

```powershell
curl http://127.0.0.1:8000/documents/updates
```

Filter by status:

```powershell
curl "http://127.0.0.1:8000/documents/updates?status=reviewed"
```

Review or accept a candidate:

```powershell
curl -X POST http://127.0.0.1:8000/documents/updates/{candidate_id}/status `
  -H "Content-Type: application/json" `
  -d "{\"review_status\":\"reviewed\",\"review_notes\":\"Verified against official source.\"}"
```

Accept a reviewed update into verified source state:

```powershell
curl -X POST http://127.0.0.1:8000/documents/source-states/accept/{candidate_id} `
  -H "Content-Type: application/json" `
  -d "{\"status\":\"current\",\"current_version\":\"2026.1\",\"verification_source_url\":\"https://example.test/official-current\",\"notes\":\"Verified current against official source.\"}"
```

List verified source states:

```powershell
curl http://127.0.0.1:8000/documents/source-states
```

The Chief/Aide brief now uses persisted documentation update candidates and suppresses items you explicitly mark as `ignored`.

### Connector Consent And Write Plans

Create a consent plan:

```powershell
curl -X POST http://127.0.0.1:8000/connectors/consent-plan `
  -H "Content-Type: application/json" `
  -d "{\"provider\":\"google_calendar\",\"access_mode\":\"read_write_review\",\"scopes\":[\"calendar.read\",\"calendar.write\"],\"user_key\":\"capt-example\",\"review_before_write\":true}"
```

Stage a future write action:

```powershell
curl -X POST http://127.0.0.1:8000/connectors/write-actions/stage `
  -H "Content-Type: application/json" `
  -d "{\"provider\":\"google_calendar\",\"user_key\":\"capt-example\",\"action_type\":\"create_event\",\"payload_summary\":\"Create drill prep reminder\",\"confirmation_token\":\"local-review-token\"}"
```

No connector route performs live mailbox/calendar reads or writes yet. Full access cannot be enabled by default.

### Commandant's Professional Reading List

List reading-list source pages:

```powershell
curl http://127.0.0.1:8000/reading-list/sources
```

List cataloged books:

```powershell
curl http://127.0.0.1:8000/reading-list/books
```

Filter to open-source/publicly available classics:

```powershell
curl "http://127.0.0.1:8000/reading-list/books?open_source_only=true"
```

Get a study summary:

```powershell
curl http://127.0.0.1:8000/reading-list/books/defence-of-duffers-drift/summary
```

The catalog stores metadata and original summaries only. It should not store copyrighted book text. Public-domain/open works such as `The Defence of Duffer's Drift` can link to sources like Project Gutenberg.

## Data Source Philosophy

The project is designed for public, official, and unclassified sources. The repository stores manifests and fetch/parsing code rather than large copyrighted publication text. RAG integrations should cite source documents and preserve source metadata, effective dates, versions, classification labels, CUI flags, and hashes.

Local user uploads are advisory working context only. They are user-provided, unverified, local, and excluded from git.

SMCR billet matching uses public Marine Corps source pages where available. Official availability and eligibility must be verified through appropriate Reserve channels.

## Configuration

`.env.example` contains local defaults:

```text
APP_NAME="SMCR Staff AI"
APP_VERSION="0.1.0"
ENVIRONMENT="local"
DATABASE_URL="sqlite:///./smcr_staff_ai.db"
VECTOR_STORE_BACKEND="local-stub"
LOCAL_CONTEXT_STORAGE_DIR="data/local_context"
SESSION_HANDOFF_STORAGE_DIR="data/local_context/session_handoffs"
LOCAL_API_KEY=""
MAX_UPLOAD_BYTES="50000000"
PUBLIC_SOURCE_ONLY="true"
```

If `LOCAL_API_KEY` is set, personal/local routes such as `/context`, `/handoffs`, `/calendar`, and `/connectors` require `X-Local-API-Key`. Leave it empty for quick local prototyping only.

`MAX_UPLOAD_BYTES` defaults to `50 MB`, which is enough for common local drill products and short training media clips. Larger media ingestion should stay local and user-managed.

SQLite is the default for quick local development. Docker Compose includes Postgres for future Postgres-ready development.

## Development

Run checks:

```powershell
ruff check .
mypy app tests
pytest
```

Run everything through Make:

```powershell
make check
```

Use fixture-based tests for parsers and network-adjacent features. Tests should not require live network access.

## Adding A New Agent

1. Create a new file in `app/services/agents/`.
2. Define metadata, allowed sources, disallowed inputs, system prompt, and placeholder behavior.
3. Register it in `app/services/agents/registry.py`.
4. Add manifest metadata in `data/seed/agent_registry.example.yaml`.
5. Add doctrine mapping in `data/seed/doctrine_manifest.example.yaml`.
6. Add tests.

## Security And Governance

Read these before expanding the project:

- `SECURITY.md`
- `DISCLAIMER.md`
- `docs/data_governance.md`
- `docs/doctrine_sources.md`
- `docs/sources/README.md`
- `docs/sources/core_marine_doctrine.md`
- `docs/sources/source_inventory_integration_plan.md`
- `docs/sources/infantry_03xx.md`
- `docs/sources/logistics_04xx.md`
- `docs/sources/correspondence_formatting.md`
- `docs/sources/commandants_reading_list.md`
- `docs/sources/tactical_handbooks_and_field_guides.md`
- `docs/usmc_history_context.md`
- `docs/staff_operating_model.md`
- `docs/roadmap.md`

The short version: keep it UNCLASSIFIED, public-source-oriented, citation-friendly, OPSEC-aware, and human-reviewed.

## Repo Search Guidance For Connected AI

If an AI tool is connected to this repo, it should search the repo for the relevant agents, tools, routes, schemas, and examples before answering non-trivial questions about capability or usage.

Start with:

1. `README.md`
2. `AGENTS.md`
3. `docs/project_purpose.md`
4. `docs/chatgpt_repo_mode.md`
5. `app/services/agents/registry.py`
6. `chatgpt_app/main.py`
7. `app/chatgpt_bridge/adapter.py`
8. `app/api/routes/`
9. `docs/examples/`
