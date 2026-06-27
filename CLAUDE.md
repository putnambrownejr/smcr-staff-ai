# SMCR Staff AI — Claude Code Context

**Read [AGENTS.md](AGENTS.md) first.** It contains the shared rules for all AI assistants
(security, source citation, project save paths, interagency knowledge, architecture).
Everything below is Claude Code-specific and extends those rules.

---

## Helping a New User

See the **Startup Wizard** section in AGENTS.md — it has the full onboarding flow.
Trigger phrases: "boot the startup wizard", "startup wizard", "getting started",
"I'm new", "help me set up", or similar.

Claude Code-specific additions to that flow:
- After the server is running, suggest loading module packs:
  Bench+Files lane → Module Packs → activate any packs in `modules/`
- Mention that Claude Code skills are available (`.claude/skills/`) for
  operator shortcuts like `/doctrine-reference` and `/scenario-runner`

---

## Claude Code-Specific Rules

- Do not install, delete, promote, sync, or rewrite skills or hooks unless explicitly asked.
- Skills live in `.claude/skills/` — they are gitignored and local-only.
- Portable knowledge belongs in `docs/`, not in skills.
