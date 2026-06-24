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

Run an agent:

```powershell
curl -X POST http://127.0.0.1:8000/agents/run `
  -H "Content-Type: application/json" `
  -d "{\"agent_id\":\"planning-advisor\",\"input\":\"Help me plan next drill weekend.\",\"context\":{\"user_role\":\"OpsO\"}}"
```

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
