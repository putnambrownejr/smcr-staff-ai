# ChatGPT App Scaffold

This repository now includes a lightweight bridge scaffold under `app/chatgpt_bridge/`.

## What It Is

It is not a full Apps SDK or MCP server yet.

It is a dependency-light bridge layer that:

- defines the first-pass ChatGPT-facing tool catalog
- maps each tool to an existing stateless `/demo/*` route
- provides an adapter that can call the live FastAPI app
- provides a stub server class that can later be registered with a real MCP runtime

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

The next implementation step is to connect this stub to a real remote MCP / ChatGPT Apps SDK runtime and test it in ChatGPT developer mode against the stateless demo routes first.
