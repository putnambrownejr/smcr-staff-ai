# API Reference

Full API usage examples for `smcr-staff-ai`. The server runs at `http://127.0.0.1:8000`.

Interactive API docs are available at `http://127.0.0.1:8000/docs` when the server is running.

---

## Health

```powershell
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "classification": "UNCLASSIFIED",
  "human_review": "required"
}
```

## Stateless Demo Mode

No prior local context required. Good for exploring repo behavior:

```powershell
curl http://127.0.0.1:8000/demo/status
curl http://127.0.0.1:8000/demo/tool-catalog
curl http://127.0.0.1:8000/demo/chief/brief
curl http://127.0.0.1:8000/demo/career/watch
```

## Agent Registry

List all agents:

```powershell
curl http://127.0.0.1:8000/agents
```

Run a local/non-scenario agent:

```powershell
curl -X POST http://127.0.0.1:8000/agents/planning-advisor/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Help me plan next drill weekend.\",\"context\":{\"user_role\":\"OpsO\"}}"
```

### External-processing preview and approval

When a configured scenario-capable agent would use an external provider, preview the
prospective messages first. This endpoint never performs the external call:

```powershell
curl -X POST http://127.0.0.1:8000/agents/planning-advisor/external-processing-preview `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Training scenario: assess the planning problem described here.\",\"context\":{\"request_is_training_or_fictional\":true}}"
```

The response includes `original_preview`, `sanitized_preview`, warning-only `findings`,
`finding_categories`, provider/model display values, expected call count, a
`payload_digest`, and an `approval_digest`. For a chain, the approval digest binds the
workflow while the payload digest identifies the currently displayed step messages.
To proceed, resubmit the unchanged request with one of these modes:

- `local_only` — do not call the provider; no digest or acknowledgement is required.
- `sanitized` — send the displayed sanitized messages.
- `original` — send the displayed original messages.

Both external modes require `acknowledged: true` and the preview's current digest:

```powershell
curl -X POST http://127.0.0.1:8000/agents/planning-advisor/run `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"Training scenario: assess the planning problem described here.\",\"context\":{\"request_is_training_or_fictional\":true},\"external_processing_approval\":{\"disclosure_mode\":\"sanitized\",\"approval_digest\":\"<64-character digest from preview>\",\"acknowledged_finding_categories\":[],\"acknowledged\":true}}"
```

Missing or stale approval returns HTTP 409 with a fresh preview under `detail.preview`.
Agent responses expose `scenario_output_status` as `not_applicable`, `template_only`,
`validated`, or `invalid`. Only `validated` structured values are passed downstream.

Chains use the same two-step pattern at `POST /agents/chain/external-processing-preview`
and `POST /agents/chain`. An externally processed chain returns `completed: false`,
`stopped_at_agent_id`, and `stopped_reason` when a required structured handoff is invalid.

## Staff Council

Run all 16 staff archetypes in parallel:

```powershell
curl -X POST http://127.0.0.1:8000/api/staff-council/capt-example `
  -H "Content-Type: application/json" `
  -d "{\"input\":\"We need to plan a battalion field exercise in Q4.\",\"echelon\":\"battalion\"}"
```

## Admin Readiness

```powershell
curl http://127.0.0.1:8000/admin/readiness/capt-example
```

## Admin Workflows

```powershell
curl -X POST http://127.0.0.1:8000/admin/workflow `
  -H "Content-Type: application/json" `
  -d "{\"workflow_type\":\"dts_voucher\",\"title\":\"Post-drill voucher\",\"facts\":[\"Receipts are complete\"]}"
```

Supported types: `dts_authorization`, `dts_voucher`, `gtcc`, `orders_review`, `admin_package`, `award_package`

## Staff Products

```powershell
curl -X POST http://127.0.0.1:8000/staff-products/draft `
  -H "Content-Type: application/json" `
  -d "{\"product_type\":\"frago\",\"topic\":\"Training-only adjustment for field-lane timeline\"}"
```

## Personnel Products

```powershell
curl -X POST http://127.0.0.1:8000/personnel/products `
  -H "Content-Type: application/json" `
  -d "{\"product_type\":\"fitrep_planning\",\"title\":\"Annual FitRep prep\",\"subject_name\":\"Capt Example\",\"occasion\":\"Annual\",\"facts\":[\"Served as battalion CommO\"],\"achievements\":[\"Built a reserve communications tracker\"]}"
```

Types: `fitrep_planning`, `fitrep_bullets`, `award_package`, `routing_package`

## Correspondence Conversion

```powershell
curl -X POST http://127.0.0.1:8000/personnel/convert-correspondence `
  -H "Content-Type: application/json" `
  -d "{\"format_type\":\"naval_letter\",\"title\":\"Travel support request\",\"purpose\":\"Request travel support.\",\"audience\":\"Battalion S-1\",\"source_text\":\"Need a formal request for travel support.\",\"references\":[\"Orders\"],\"enclosures\":[\"Orders\",\"Travel estimate\"]}"
```

Formats: `naval_letter`, `memorandum`, `endorsement`, `routing_package`, `point_paper`, `professional_email`

## Drill Prep

```powershell
curl -X POST http://127.0.0.1:8000/drill-plans/capt-example `
  -H "Content-Type: application/json" `
  -d "{\"drill_date\":\"2026-07-12\",\"key_events\":[\"Range qualification\",\"Admin call\"]}"
```

## Training / ORM

```powershell
curl -X POST http://127.0.0.1:8000/training/scenario `
  -H "Content-Type: application/json" `
  -d "{\"scenario_type\":\"staff_drill\",\"title\":\"Battalion planning drill\",\"training_objective\":\"Practice decision-making.\",\"constraints\":[\"Three-hour window\"]}"

curl -X POST http://127.0.0.1:8000/training/orm `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Range day ORM\",\"activity\":\"Live-fire rifle qualification\",\"hazards\":[\"Negligent discharge\",\"Heat injury\"],\"controls\":[\"Safety brief\",\"RSO oversight\",\"Hydration plan\"]}"
```

## Unit PT and Cadence Library

The unit-PT planner accepts 5–50 participants and returns deterministic training blocks, S-3/S-4/SgtMaj/Fitness reviews, an editable ORM matrix, warnings, and official-source labels. It does not replace an FFI, CPTR, medical provider, official PFT/CFT monitor, or command risk acceptance.

```powershell
curl -X POST http://127.0.0.1:8000/fitness/unit-pt/plan `
  -H "Content-Type: application/json" `
  -d '{"participant_count":30,"objective":"CFT preparation","duration_minutes":60,"location":"unit training area","include_cadence":true}'

curl "http://127.0.0.1:8000/cadences/capt-example?include_adult=false"

curl -X POST http://127.0.0.1:8000/cadences/capt-example `
  -H "Content-Type: application/json" `
  -d '{"user_key":"capt-example","title":"My cadence","text":"Move with purpose.","rating":"clean"}'
```

Adult-labeled cadences are opt-in. The service rejects slurs, targeted harassment, hazing, sexual violence, and targeted degradation regardless of label.

## FitRep Profile Analytics

```powershell
curl http://127.0.0.1:8000/fitreps/capt-example
curl http://127.0.0.1:8000/fitreps/capt-example/analytics

curl -X POST http://127.0.0.1:8000/fitreps/capt-example/reports `
  -H "Content-Type: application/json" `
  -d '{"user_key":"capt-example","period_end":"2026-06-30","grade":"Capt","rs_label":"RS-A","relative_value":92.4}'
```

Document uploads use `/fitreps/{user_key}/imports/preview` followed by `/fitreps/{user_key}/imports/confirm`. The preview is intentionally conservative and does not invent missing dates, marks, or profile values. Analytics are descriptive and do not predict promotion or selection.

## Travel / GTCC Workspace

```powershell
curl http://127.0.0.1:8000/travel-cases/capt-example
curl -X POST http://127.0.0.1:8000/travel-cases/capt-example `
  -H "Content-Type: application/json" `
  -d '{"user_key":"capt-example","title":"Annual Training travel","destination":"Quantico"}'
```

Travel expenses, payments, and balance checks are user-entered and may be stale. The application does not connect to Citi or request card credentials. Every “check your GTCC” flow links to the CitiManager cardholder login.

## Chief of Staff Capability Gateway

The Chief has a closed set of typed operations. It can read domain summaries, search readable repository source files within the repository root, and explicitly append Travel/GTCC, FitRep, RS-profile, goal, or cadence records. It has no generic shell or unrestricted filesystem writer. Private projects and tool/cache directories are excluded from search. Each append returns a single-use Undo token.

```powershell
curl http://127.0.0.1:8000/chief/capabilities/capt-example/summary

curl -X POST http://127.0.0.1:8000/chief/capabilities `
  -H "Content-Type: application/json" `
  -d '{"user_key":"capt-example","operation":"append_cadence","payload":{"title":"New cadence","text":"Move with purpose."}}'

curl -X POST http://127.0.0.1:8000/chief/capabilities/undo `
  -H "Content-Type: application/json" `
  -d '{"user_key":"capt-example","undo_token":"TOKEN_FROM_APPEND"}'
```

DRAFT — Verify all references against current official sources before acting.

## PKI / CAC Troubleshooting

```powershell
curl -X POST http://127.0.0.1:8000/admin/pki-troubleshooting `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"MarineNet CAC login issue\",\"issue_type\":\"browser_auth_issue\",\"symptoms\":[\"Certificate prompt never appears\"],\"browser\":\"Chrome\",\"affected_systems\":[\"MarineNet\"],\"on_government_furnished_equipment\":false}"
```

## Connector Planning

```powershell
curl -X POST http://127.0.0.1:8000/connectors/chief-digest-plan `
  -H "Content-Type: application/json" `
  -d "{\"user_key\":\"capt-example\",\"consents\":[{\"provider\":\"google_calendar\",\"access_mode\":\"read_only\",\"user_key\":\"capt-example\",\"enabled\":false}],\"calendar_events\":[{\"provider\":\"google_calendar\",\"title\":\"Drill weekend muster\",\"start_at\":\"2026-06-06T08:00:00Z\",\"location\":\"NOSC New Orleans\"}],\"email_messages\":[]}"
```

## Pre-Push Privacy Review

```powershell
curl -X POST http://127.0.0.1:8000/privacy/pre-push-review `
  -H "Content-Type: application/json" `
  -d "{}"
```

## Session Handoffs

```powershell
curl http://127.0.0.1:8000/handoffs/capt-example
curl -X POST http://127.0.0.1:8000/handoffs/capt-example/draft-update `
  -H "Content-Type: application/json" `
  -d "{\"display_name\":\"Capt Example\",\"rank\":\"Captain\"}"
```

## Local Context Storage

```powershell
curl http://127.0.0.1:8000/local-context/capt-example
curl -X POST http://127.0.0.1:8000/local-context/capt-example `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Unit SOP\",\"content\":\"Example content\",\"category\":\"sop\"}"
```

## Action Tracking

```powershell
curl "http://127.0.0.1:8000/actions?user_key=capt-example&priority=high"
```

## MARADMIN / Message Watch

```powershell
curl http://127.0.0.1:8000/maradmin/latest
curl http://127.0.0.1:8000/messages/watch
```

## Custom MOS Recipes

```powershell
curl http://127.0.0.1:8000/api/custom-mos-recipes/capt-example
curl -X POST http://127.0.0.1:8000/api/custom-mos-recipes/capt-example `
  -H "Content-Type: application/json" `
  -d "{\"parent_agent_id\":\"infantry-03xx\",\"mos_code\":\"0302\",\"mos_title\":\"Infantry Officer\",\"focus_areas\":[\"Company command\",\"Training management\"]}"
```
