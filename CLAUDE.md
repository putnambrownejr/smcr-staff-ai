# SMCR Staff AI — Claude Code Context

**Read [AGENTS.md](AGENTS.md) first.** It contains the shared rules for all AI assistants
(security, source citation, project save paths, interagency knowledge, architecture).
Everything below is Claude Code-specific and extends those rules.

---

## Helping a New User

If someone just cloned this repo and opened you (the AI assistant), do this:

1. **Start the server** — run `start.bat` (Windows) or `./start.sh` (Mac/Linux) in a terminal
2. **Open the dashboard** — http://localhost:8000/dashboard
3. **Workspace auto-loads** — profile ID is generated on first visit, stored in the browser
4. **Set up their profile** — Workspace tab → Profile & preferences → fill in billet, unit, MOS
5. **Load module packs** — Bench+Files lane → Module Packs → activate any packs in `modules/`

---

## Claude Code-Specific Rules

- Do not install, delete, promote, sync, or rewrite skills or hooks unless explicitly asked.
- Skills live in `.claude/skills/` — they are gitignored and local-only.
- Portable knowledge belongs in `docs/`, not in skills.
