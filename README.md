# smcr-staff-ai

`smcr-staff-ai` is an UNCLASSIFIED, open-source-ready FastAPI prototype for AI-enabled Selected Marine Corps Reserve staff workflows. It is designed for SMCR officers, staff officers, and company/battalion/regimental staff who need advisory drafting support, public-source lookup, reserve administration helpers, local context storage, and future doctrine-grounded RAG.

This project is unofficial, not endorsed by the Marine Corps or Department of Defense, and not authoritative. All outputs are advisory drafts requiring human review.

## Safety First

Do not submit classified information, CUI, secrets, credentials, COMSEC, keying material, real frequencies, call signs, current operational movement details, sensitive unit plans, or unnecessary PII.

The application includes basic runtime guardrails for likely sensitive inputs, but those checks are not a substitute for human judgment, OPSEC review, or official policy. The system should produce checklists, drafts, and recommendations, not orders or official guidance.

## Current Capabilities

| Capability | What it does now | Status |
| --- | --- | --- |
| Agent registry | Lists and runs placeholder staff/MOS agents with structured responses, warnings, confidence, citations, and follow-up questions. | Working stub |
| Chief of Staff / Aide de Camp | Coordinates drill prep, MARADMIN/news awareness, session handoffs, and future email/calendar triage. | Working scaffold |
| Chief/Aide orchestration brief | Combines session handoff, local personal docs, drill plans, MARADMIN-driven source updates, and reading suggestions into one advisory triage brief. | Working local orchestrator |
| Text summarizer / checklist API | Turns pasted text into a local summary, due-outs, action items, checklist, and follow-up questions without storing the input. | Working local analysis |
| Staff council | Vets ideas through company, battalion, and division/group staff roles, with S-2/G-2 tied to OSINT. Includes round-robin review. | Working scaffold |
| Staff products | Builds advisory scaffolds for OPORDs, WARNOs, FRAGOs, SITREPs, AARs, naval letters, memos, and endorsements. | Working scaffold |
| Session handoffs | Stores minimum necessary local user context for PME, FitRep, admin, drill, and preference reminders. | Working local storage |
| Local context storage | Lets users upload files/notes, RQS/BIO references, and drill templates as advisory local context without changing doctrine, org, exercise, agent, or canonical document structure. | Working local storage |
| Personal document organizer | Lists local RQS/BIO/orders/travel/PME-style uploads by type and flags PII/local-retention warnings. | Working local organizer |
| Career opportunity tracker | Stores ADOS and SMCR BIC opportunities locally, ranks them against a user profile, and surfaces them in the Chief/Aide brief. | Working local tracker |
| Drill prep planner | Turns a drill date into advisory prep tasks, can use templated local key events, persists plans locally, and exports `.ics` calendar content. | Working local planner |
| SMCR BIC discovery | Lists official public billet source pages, parses public billet tables/cards where available, discovers Reserve Hub links, and ranks billets against user MOS/rank/location/keywords. | Working parser/recommender with live-source caveats |
| OSINT trend aggregation | Aggregates user-supplied trusted public-source news/social trend summaries with citations, counterarguments, and confidence weighting. | Working source-evaluation agent |
| Vetted social ingestion | Normalizes public news/social trend records into OSINT/deep-research-ready source items without unrestricted scraping. | Working connector |
| Professional reading catalog | Tracks Commandant's Reading List sources, archive references, open-source classics, and study summaries. | Working catalog |
| USMC history context | Provides an easy-access Marine Corps history and heritage study reference for agent context and PME prompts. | Markdown reference |
| Org awareness | Loads example MARFORRES-style hierarchy and answers unit chain lookups. | Working example data |
| Exercise cadence | Provides typical/advisory exercise and battle rhythm examples. | Working example data |
| RSS/MARADMIN parsing | Parses local RSS XML fixtures and tags messages by staff relevance. | Working parser; live ingestion is later |
| RAG foundations | Includes document/chunk models, chunking, local embedding stub, vector-store stub, doctrine manifest validation, and citation-preserving local RAG pipeline. | Ready for expansion |

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
    billets/           SMCR billet recommendation
    calendar/          Drill-prep planner and calendar provider stubs
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
MAX_UPLOAD_BYTES="10000000"
PUBLIC_SOURCE_ONLY="true"
```

If `LOCAL_API_KEY` is set, personal/local routes such as `/context`, `/handoffs`, `/calendar`, and `/connectors` require `X-Local-API-Key`. Leave it empty for quick local prototyping only.

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
