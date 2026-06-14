# Quickstart

SMCR Staff AI is a local command-post dashboard for USMC reserve staff workflows —
session handoffs, watch feeds, bench notebooks, planning tools, and more.
Runs entirely on your machine; no cloud dependency required at runtime.

---

## Prerequisites

- **Python 3.12+** — [python.org](https://www.python.org/downloads/)
- **uv** — `pip install uv` (or [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/))

_Docker users: skip the above and see the Docker section below._

---

## 1. Clone

```bash
git clone https://github.com/putnambrownejr/smcr-staff-ai.git
cd smcr-staff-ai
```

## 2. Start

**Windows:**
```bat
start.bat
```

**Mac / Linux:**
```bash
./start.sh
```

Both scripts install dependencies and start the server automatically.

## 3. Open the Dashboard

[http://localhost:8000/dashboard](http://localhost:8000/dashboard)

Your workspace opens automatically on first visit — no account creation needed.
A unique profile ID is generated and stored in your browser.

---

## Connect Your AI Assistant

For the best experience, open your AI coding assistant in the repo directory.
The project includes a `CLAUDE.md` at the root that orients Claude Code (and other
compatible assistants) to help you use and extend the app.

**Claude Code:**
```bash
cd smcr-staff-ai
claude
```

**Other assistants** (Cursor, Copilot, etc.) — open the repo folder in your IDE.
The project-level `CLAUDE.md` and `ARCHITECTURE.md` are the best starting points.

---

## Docker (Alternative)

```bash
docker compose up
```

Opens at the same address. User data persists in a named Docker volume (`smcr-data`).
Module packs in `modules/` are mounted read-only into the container.

---

## First-Time Setup in the Dashboard

1. **Profile** — Workspace tab → Profile & preferences → enter your billet, unit, MOS
2. **Module packs** — Bench+Files lane → Module Packs → activate any packs in `modules/`
3. **Optional passkey** — Workspace → Advanced settings → set a passkey if sharing your machine

---

## Five Lanes

| Lane | Purpose |
|------|---------|
| **Overview** | Readiness posture, Act Now queue, history fact, command-post summary |
| **Watch** | MARADMIN feed, source watch, reading tracker |
| **Bench + Files** | Section bench notebook (configurable), uploaded context files, module packs |
| **Workflows** | Staff product scaffolds and planning-cell tools |
| **Workspace** | Profile, settings, session handoff notes |

---

## Running Tests

```bash
uv run pytest tests/ -q          # unit + integration
uv run pytest -m e2e tests/e2e/  # E2E — requires: playwright install chromium + running server
```

---

## Environment Variables

Copy `.env.example` to `.env` to customize storage paths, passkey, and other settings.
All settings have sensible defaults — `.env` is optional for local single-user use.
