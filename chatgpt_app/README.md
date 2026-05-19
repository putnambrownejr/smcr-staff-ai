# SMCR Staff AI ChatGPT App

This is a first-pass local ChatGPT app surface for `smcr-staff-ai`.

It is designed to feel more like the Coach Dave style experience:

- a few clear top-level tools
- no Swagger exposure for ordinary use
- your existing FastAPI backend stays the system of record
- ChatGPT becomes the conversational front door

## Archetype

Primary archetype: `tool-only`

Why:

- the backend workflows are already strong and mostly textual
- the highest-value first move is hiding route sprawl, not building a widget first
- local/private user context is easier to protect when the surface stays small

## Tools Exposed

- `build_staff_package`
- `draft_staff_product`
- `build_frago_to_conop`
- `build_training_case_study`
- `build_tdg`
- `build_infantry_training_package`
- `build_mission_analysis`
- `build_planning_cell`
- `build_lone_planner`
- `build_assisted_section_estimates`
- `build_staff_update_cycle`
- `run_infantry_03xx_advisor`
- `run_patrolling_refresher`
- `run_blank_fire_urban_lane`
- `run_leader_rehearsal_oic_worksheet`
- `run_opt_facilitator`
- `run_sja_military_justice_advisor`
- `run_njp_issue_spotting_worksheet`
- `run_military_justice_routing_checklist`
- `run_red_team_assumptions_challenge`
- `run_assessment_learning_advisor`
- `run_writing_briefing_coach`
- `run_joint_interagency_frame_advisor`
- `list_staff_agents`
- `run_staff_agent`
- `build_chief_brief`
- `build_next_drill_readiness`
- `build_walk_in_brief_pack`
- `career_watch`
- `admin_readiness`
- `build_admin_workflow`
- `build_handoff_reminder_plans`
- `build_external_ai_packet`
- `get_active_user_context`
- `set_active_user_context`

`build_tdg` is the S-3 wargaming / tactical-decision-game lane. It is meant to pressure-test assumptions,
force decisions early, and expose reserve-specific friction before the real event does.

`build_infantry_training_package` is the training-safe 03 familiarization lane. Use it when the user wants a
modified urban or infantry-flavored package for non-03 Marines, especially around blanks, MOUT sites, scope
control, leader rehearsals, and AAR discipline without pretending it is advanced CQB instruction.

`build_mission_analysis` is the mission-analysis worksheet lane. Use it when the user needs specified tasks,
implied tasks, essential tasks, assumptions, information requirements, and staff-estimate due-outs before the
staff starts polishing products.

`build_planning_cell` is the fuller planning-rhythm lane. Use it when the user wants mission analysis, a
deliberate-vs-compressed planning recommendation, an assumption log, a commander decision log, due-outs,
red-team focus, and the linked running estimate/CUB/CPB package together.

`build_lone_planner` is the thin-bench continuity lane. Use it when the user is covering down alone or outside
their lane and needs a walk-in brief, likely blind spots, cross-lane asks, immediate actions, and a linked
planning-cell package that keeps the frame honest.

`build_assisted_section_estimates` is the cross-lane gap-cover lane. Use it when the user has only partial
staff coverage and needs disciplined scaffolds for missing lanes like S-1/Admin, S-4, S-6, medical, XO/Chief,
or SEL before briefing the XO or commander.

`build_staff_update_cycle` is the recurring staff-rhythm lane. It takes section updates and turns them into
a linked running estimate, CUB, and CPB so the user can move from “what changed?” to “what does the commander
need to hear or decide?” without rebuilding the frame every time.

`build_walk_in_brief_pack` is the cold-start continuity lane. Use it when the user needs the fastest honest
picture before a sync, call, or drill walk-in: what changed, what may be stale, what decisions are still open,
and what needs to be carried in their head before they step into the room.

`run_infantry_03xx_advisor` is the S-3-family infantry thinking lane. Use it when the user wants infantry-
flavored training help without pretending every event is a formal 03xx qualification package.

`run_patrolling_refresher` is the simple patrolling lane. Use it for fundamentals, control measures, leader
checks, reporting, and training-safe repetition.

`run_blank_fire_urban_lane` is the controlled urban lane. Use it for blanks, MOUT sites, sectors, reports,
casualty actions, supervision, and what should stay dry until the leaders prove control.

`run_leader_rehearsal_oic_worksheet` is the execution-control lane. Use it when the user needs a compact OIC
worksheet around intent, roles, control measures, stop-training criteria, safety, medical checks, and AAR setup.

`run_sja_military_justice_advisor` is the clean front door for command legal issue-spotting. Use it when the
user needs SJA-shaped help on NJP, UCMJ, courts-martial process awareness, Reserve-status jurisdiction questions,
or legal routing without pretending the tool is a lawyer.

`run_njp_issue_spotting_worksheet` is the compact NJP lane. Use it when the user wants the question broken into
authority, jurisdiction, accused advice, punishments, Reserve concerns, UPB discipline, appeal exposure, and
what must go to the real SJA now.

`run_military_justice_routing_checklist` is the compact handoff lane. Use it when the user needs a fast command
check on whether the matter belongs with SJA, defense, VLC, trial services, or another military justice channel,
and what minimum clean handoff package should be prepared.

`run_opt_facilitator` is the cleaner front door for mission analysis and OPT conduct. Use it when the staff
needs to keep a visible assumption log, decision log, question log, and due-out tracker instead of jumping
straight to slides or orders.

`run_red_team_assumptions_challenge` is the fast pressure-test lane for COAs, plans, and briefs. Use it to
challenge weak assumptions, fake alternatives, and quiet groupthink before the commander sees the product.

`run_assessment_learning_advisor` is the learning-loop lane. Use it when you want to tie an event, AAR,
corrective actions, and next-drill follow-through together instead of letting lessons die after the brief.

`run_writing_briefing_coach` is the quick discipline lane for briefs and products. Use it when a CPB, CUB,
decision brief, or draft product needs to be cleaner about audience, decision, evidence, and what belongs in
backup.

`run_joint_interagency_frame_advisor` is the external-frame lane. Use it when the Marine-only view is too
narrow and the staff needs help with command relationships, outside actors, and coordination assumptions.

`draft_staff_product` is now also the right lane for briefing content when you want a deck outline that behaves
like a real staff brief instead of a generic AI slide dump. Use `decision_brief` or `command_update_brief`
for slide-by-slide content discipline first, then convert to slides later if needed.

`set_active_user_context` is the quick way to tell the app "treat me like I am at this kind of unit right now"
without overwriting the longer-term handoff. Staff agents can pick that up automatically when the run includes
the same `user_key`.

`build_external_ai_packet` is the safe way to prepare local context for an external model such as Claude,
Gemini, Grok, Copilot, or a generic government-hosted environment. It returns a scrubbed packet, warnings,
redacted fields, and a provider-shaped recommended share prompt.

## How It Works

This app server does not reimplement the staff logic.

Instead it calls the existing local backend through the bridge adapter in:

- [C:\smcr-staff-ai\app\chatgpt_bridge\adapter.py](C:/smcr-staff-ai/app/chatgpt_bridge/adapter.py)

That keeps the architecture sane:

- `smcr-staff-ai` owns the actual workflow logic
- the ChatGPT app owns the small tool surface

## Local Run

1. Start the main backend first.

   The easiest way is:

   - [C:\smcr-staff-ai\scripts\start-local.cmd](C:/smcr-staff-ai/scripts/start-local.cmd)

2. Install the small app-server dependency set:

```powershell
pip install -r .\chatgpt_app\requirements.txt
```

3. Start the app surface:

```powershell
uvicorn chatgpt_app.main:app --host 0.0.0.0 --port 8001
```

The MCP endpoint will be:

- `http://127.0.0.1:8001/mcp`

The easier path is to use the helper launcher from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-chatgpt-app.ps1 -Detached
```

Or just double-click:

- [C:\smcr-staff-ai\scripts\start-chatgpt-app.cmd](C:/smcr-staff-ai/scripts/start-chatgpt-app.cmd)

The helper will:

- start from the correct repo directory
- pick a free local port starting at `8006`
- try to detect the live backend automatically
- print the final local MCP URL

## Optional Local API Key

If your main backend uses `LOCAL_API_KEY`, set this before running the app server:

```powershell
$env:SMCR_STAFF_AI_LOCAL_API_KEY="your-local-key"
```

## Pointing At A Different Backend

If your main backend is on a different port:

```powershell
$env:SMCR_STAFF_AI_BACKEND_URL="http://127.0.0.1:8005"
```

Or pass it directly:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-chatgpt-app.ps1 -BackendUrl http://127.0.0.1:8005
```

## ChatGPT Developer Mode Flow

For local testing, the typical flow is:

1. run the main backend
2. run this app server
3. expose `http://127.0.0.1:8001/mcp` through an HTTPS tunnel
4. add that tunneled MCP URL in ChatGPT developer mode

To stop the app server later:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-chatgpt-app.ps1
```

## What This Is Not Yet

This is not yet:

- a full hosted public app
- a widget-heavy UI experience
- a multi-user deployment

It is the clean first step away from Swagger and toward a real ChatGPT-native interface.
