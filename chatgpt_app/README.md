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
- `build_staff_update_cycle`
- `list_staff_agents`
- `run_staff_agent`
- `build_chief_brief`
- `build_next_drill_readiness`
- `career_watch`
- `admin_readiness`
- `build_admin_workflow`
- `build_handoff_reminder_plans`
- `build_external_ai_packet`
- `get_active_user_context`
- `set_active_user_context`

`build_tdg` is the S-3 wargaming / tactical-decision-game lane. It is meant to pressure-test assumptions,
force decisions early, and expose reserve-specific friction before the real event does.

`build_staff_update_cycle` is the recurring staff-rhythm lane. It takes section updates and turns them into
a linked running estimate, CUB, and CPB so the user can move from “what changed?” to “what does the commander
need to hear or decide?” without rebuilding the frame every time.

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
