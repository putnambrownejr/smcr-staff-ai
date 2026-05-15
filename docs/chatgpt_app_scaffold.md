# ChatGPT App Scaffold

This repository now includes both:

- a lightweight bridge scaffold under `app/chatgpt_bridge/`
- a first-pass local app server under `chatgpt_app/`

## What It Is

The bridge layer is a dependency-light adapter that:

- defines the first-pass ChatGPT-facing tool catalog
- maps each tool to an existing stateless `/demo/*` route
- provides an adapter that can call the live FastAPI app
- provides a stub server class that can later be registered with a real MCP runtime

The local app server is the next step:

- it exposes a curated MCP tool surface on top of the live backend
- it is Python-first and follows the official FastMCP example shape
- it hides Swagger for normal use
- it favors a few strong workflows over route-by-route exposure

## Files

- `app/chatgpt_bridge/schemas.py`
- `app/chatgpt_bridge/catalog.py`
- `app/chatgpt_bridge/adapter.py`
- `app/chatgpt_bridge/server_stub.py`

## Why This Shape

This keeps the first integration step small and reversible:

- no private/local user context is exposed
- no auth model is assumed yet
- the tool surface is explicit and testable
- later MCP or Apps SDK wiring can wrap the existing stub instead of reinventing tool behavior

## Intended First Tools

- `chief_brief_demo`
- `career_watch_demo`
- `summarize_text_demo`
- `draft_staff_product_demo`
- `run_staff_agent_demo`

## Next Step

The next implementation step is to connect the local `chatgpt_app/` surface to ChatGPT developer mode through an HTTPS tunnel, test the tool behavior in conversation, and then decide whether the next promotion is:

1. a richer local personal-use app
2. a hosted remote MCP surface
3. a fuller ChatGPT App with UI/widget work
