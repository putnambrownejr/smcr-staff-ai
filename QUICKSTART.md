# Quickstart

SMCR Staff AI is a local command-post dashboard for USMC reserve staff workflows.
Runs entirely on your machine — no cloud dependency at runtime.

---

## Which path is right for me?

| I want to… | Use |
|---|---|
| Clone and run with minimal setup (most users) | `start.bat` (Windows) or `./start.sh` (Mac/Linux) |
| Check what I need to install first | `setup-check.bat` (Windows) or `./setup-check.sh` (Mac/Linux) |
| Not install Python locally | Docker — see below (requires Docker Desktop) |

---

## Prerequisites

The `start.bat` / `start.sh` path needs three things. Run `setup-check.bat` or
`./setup-check.sh` to check what's already installed and get exact install commands for anything missing.

### 1. Git

Needed to clone the repo.

| Platform | Install command |
|---|---|
| Windows | `winget install Git.Git` |
| Mac | `brew install git` |
| Linux | `sudo apt install git` |
| Any | [git-scm.com/downloads](https://git-scm.com/downloads) |

> No git yet? Download the ZIP from GitHub (green **Code** button → **Download ZIP**), unzip it, and open a terminal in that folder.

### 2. Python 3.12+

| Platform | Install command |
|---|---|
| Windows | `winget install Python.Python.3.12` |
| Mac | `brew install python@3.12` |
| Linux | `sudo apt install python3.12` |
| Any | [python.org/downloads](https://www.python.org/downloads/) |

Verify: `python --version` should show **3.12 or higher**.

### 3. uv (dependency manager)

Fast Python package manager — handles all dependencies automatically.

| Platform | Install command |
|---|---|
| Windows (PowerShell) | `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` |
| Mac / Linux | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Any (if Python installed) | `pip install uv` |

> **Let your AI assistant help:** If you have Claude Code, Copilot, Cursor, or another AI
> coding assistant, open it in this repo folder and say:
> *"Help me install the prerequisites listed in QUICKSTART.md."*
> It can walk you through each step on your specific OS.

---

## 1. Clone the repo

```bash
git clone https://github.com/putnambrownejr/smcr-staff-ai.git
cd smcr-staff-ai
```

## 2. Check prerequisites (recommended for first-timers)

**Windows:**
```bat
setup-check.bat
```

**Mac / Linux:**
```bash
chmod +x setup-check.sh
./setup-check.sh
```

This checks for Git, Python 3.12+, and uv — and prints exact install commands for anything
missing. If everything is present it will offer to launch the server for you.

## 3. Start the server

**Windows:**
```bat
start.bat
```

**Mac / Linux:**
```bash
./start.sh
```

Both scripts install dependencies and start the server. First run takes ~30 seconds while
packages download. You should see `Uvicorn running on http://0.0.0.0:8000` when it's ready.

## 4. Open the dashboard

[http://localhost:8000/dashboard](http://localhost:8000/dashboard)

Your workspace opens automatically on first visit — no account creation needed.
A unique profile ID is generated and stored in your browser.

---

## Docker (Alternative)

Use Docker if you prefer not to install Python locally.

**Requires:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac)
or Docker Engine (Linux).

```bash
docker compose up
```

Opens at the same address. User data persists in a named Docker volume (`smcr-data`).
Module packs in `modules/` are mounted read-only into the container.

---

## Connect Your AI Assistant

For the best experience, open your AI coding assistant in the repo directory.
The project includes a `CLAUDE.md` that orients Claude Code and compatible assistants.

**Claude Code:**
```bash
cd smcr-staff-ai
claude
```

**Other assistants (Cursor, Copilot, etc.):** open the repo folder in your IDE.
`CLAUDE.md` and `ARCHITECTURE.md` are the best starting points.

---

## First-Time Setup in the Dashboard

1. **Profile** — Workspace tab → Profile & preferences → enter billet, unit, MOS
2. **Session handoff** — Workspace tab → Session Handoff → add PME, FitRep, and drill dates so the Chief brief has context
3. **Module packs** — Bench+Files lane → Module Packs → activate any packs in `modules/`
4. **Optional passkey** — Workspace → Advanced settings → set a passkey if sharing your machine

---

## Five Lanes

| Lane | Purpose |
|---|---|
| **Overview** | Readiness posture, Act Now queue, history fact, command-post summary |
| **Watch** | MARADMIN feed, source watch, reading tracker |
| **Bench + Files** | Section bench notebook (configurable), uploaded context files, module packs |
| **Workflows** | Staff product scaffolds and planning-cell tools |
| **Workspace** | Profile, settings, session handoff notes |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `start.bat` says "uv not found" | Run `pip install uv` then retry |
| `python --version` shows 3.10 or 3.11 | Upgrade: `winget install Python.Python.3.12` |
| Port 8000 already in use | Stop whatever is running on 8000, or change the port in `start.bat` |
| Dashboard won't load | Confirm the server is running — look for `Uvicorn running` in the terminal |
| `setup-check.sh`: permission denied | Run `chmod +x setup-check.sh` first |

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
