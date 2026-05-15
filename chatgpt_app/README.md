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
- `list_staff_agents`
- `run_staff_agent`
- `build_chief_brief`
- `career_watch`
- `admin_readiness`
- `build_admin_workflow`

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

## ChatGPT Developer Mode Flow

For local testing, the typical flow is:

1. run the main backend
2. run this app server
3. expose `http://127.0.0.1:8001/mcp` through an HTTPS tunnel
4. add that tunneled MCP URL in ChatGPT developer mode

## What This Is Not Yet

This is not yet:

- a full hosted public app
- a widget-heavy UI experience
- a multi-user deployment

It is the clean first step away from Swagger and toward a real ChatGPT-native interface.
