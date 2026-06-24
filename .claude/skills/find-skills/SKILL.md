---
name: find-skills
description: Discover available agents, skills, and capabilities within smcr-staff-ai. Searches the local agent registry, project skills, Staff Council, custom MOS recipes, and optionally external skill registries. Use when asked "what can this project do", "which agent handles X", "find a skill for X", or "what's available."
---

# Find Skills — smcr-staff-ai

Discover what this project can do by searching across all local capability registries — agents, skills, Staff Council, and custom MOS recipes — before looking externally.

## When to Use

- "What agent handles X?" / "Who do I ask about Y?"
- "What skills are available?" / "What can this project do?"
- "Is there an agent for [topic]?"
- "Find a skill for [task]"
- Before building something new — check if it already exists

## Search Order

### 1. Local Agent Registry (primary)

Search the 35 registered agents in `app/services/agents/registry.py`:

```bash
# List all agent IDs and names
grep -r 'id="' app/services/agents/ --include="*.py" -h
grep -r 'name="' app/services/agents/ --include="*.py" -h
```

**19 standalone agents** — specialized advisors (fires, infantry, planning, ORM, etc.)
**16 staff archetypes** — `staff-{role}` pattern (s1, s2, opso, s4, s6, sja, pao, etc.)

Each agent has:
- `id` — the routing key
- `name` — display name
- `system_prompt` — describes what the agent covers
- `allowed_sources` — references it can cite

### 2. Staff Council

The Staff Council at `/api/staff-council/{user_key}` runs all 16 staff archetypes in parallel for cross-lane deliberation. It's not a single agent — it's a multi-agent orchestration layer.

### 3. Custom MOS Recipes

Users can create custom MOS advisor recipes at `/api/custom-mos-recipes/{user_key}`. These extend a parent agent with MOS-specific focus areas. Check if the user has recipes:

```bash
# See the valid parent agents and recipe structure
cat app/api/routes/custom_mos_recipes.py
```

### 4. Project Skills

Search `.claude/skills/` for project-level Claude Code skills:

```bash
ls .claude/skills/
```

Each skill has a `SKILL.md` with name, description, and when-to-use guidance.

### 5. Global Skills (if local search finds nothing)

Search the user's global skills at `~/.claude/skills/` — these are personal skills that work across all projects.

### 6. External Registries (last resort)

Only if nothing local fits, search external registries:
- skills.sh API: `https://www.skills.sh/api/search?q=<query>`
- GitHub: repos tagged `claude-skill` or `claude-code-skill`

## How to Present Results

**Deliver a verdict, not a menu.**

- Name the best match with a one-sentence why.
- If the match is a local agent, include its `id` so the user can invoke it directly.
- If multiple agents are relevant, explain which covers which aspect.
- If the Staff Council is the right tool, say so and explain why a single agent won't suffice.
- If nothing fits, say so plainly and offer to build it.

## Example Queries and Routing

| User asks about... | Route to |
|---|---|
| "legal issue" | `staff-sja` |
| "logistics for AT" | `staff-s4` |
| "fire support" | `fires-advisor` |
| "air support" | `ace` |
| "ground maneuver" | `gce` |
| "sustainment" | `lce` or `staff-s4` (depends on scope) |
| "full staff estimate" | Staff Council |
| "CAC not working" | `pki-cac-troubleshooter` |
| "write an OPORD" | `staff-products` |
| "plan a training event" | `planning-advisor` or `staff-opso` |
| "uniform inspection" | `uniform-advisor` |
| "risk assessment" | `orm-risk-management` |
| "design review" | `murder-board` skill |
| "what to automate" | `automated-skill-builder` skill |
| "at division level" | `echelon-context` skill (sets echelon modifier) |
| "how does this differ at regiment" | `echelon-context` skill (comparison mode) |
| "add a new agent" | `agent-scaffolder` skill (multi-file checklist) |
| "compare agent responses" | `scenario-runner` skill |
| "check source references" | `source-audit` skill |
| "what pub covers fires" | `doctrine-reference` skill |
| "which MCDP" | `doctrine-reference` skill |

## Rules

- **Local first.** Always search the project's agent registry before looking externally.
- **Be specific.** Don't say "there might be an agent" — grep the registry and confirm.
- **Explain coverage boundaries.** If an agent partially covers the need, say what's covered and what isn't.
- **UNCLASSIFIED only.** Do not search for or recommend capabilities that would handle classified information.
