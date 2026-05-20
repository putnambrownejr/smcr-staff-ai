# Optional Legacy Surfaces

This repo has a clear primary path now:

- local FastAPI backend
- local browser dashboard
- local-only user context and continuity stores

The following surfaces still exist, but are **quarantined as optional/legacy** for now:

## 1. ChatGPT App / MCP Server

Paths:

- `chatgpt_app/`
- `app/chatgpt_bridge/`
- `scripts/start-chatgpt-app.ps1`
- `scripts/start-chatgpt-app.cmd`

Why it is quarantined:

- it is useful for experimentation
- it is not required for the core SMCR workflow
- it adds extra runtime complexity, ports, and tool-surface maintenance
- the main product value now lives in the local backend and dashboard first

Current posture:

- keep it working
- do not treat it as the default user path
- do not design the main repo around it
- remove later only if it becomes clear it is dead weight

## 2. Docker Local Path

Paths:

- `Dockerfile`
- `docker-compose.yml`
- `docs/docker_local.md`
- `docker/`

Why it is quarantined:

- it is useful for containerized local runs and future packaging
- it is not the main value path for day-to-day SMCR use
- it creates extra operational surface that should not drive ordinary workflow decisions

Current posture:

- keep it available
- treat it as optional
- do not let Docker-specific decisions distort the simpler local-backend path

## Repo Rule Going Forward

Default build and UX decisions should optimize for:

1. local backend
2. browser dashboard
3. local-only continuity and storage

Only after that should changes consider:

1. ChatGPT app / MCP compatibility
2. Docker/container convenience

That keeps the core product centered on SMCR continuity and staff support instead of tool-surface sprawl.
