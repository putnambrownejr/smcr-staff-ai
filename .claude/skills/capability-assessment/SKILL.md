---
name: capability-assessment
description: Three-tier visual assessment of all agents, skills, and key capabilities. Rates general usefulness, out-of-box capability, and user-tuned capability on a 1-10 scale with an interactive heatmap. Use for periodic health checks, enrichment gap analysis, or after major changes.
---

# Capability Assessment — smcr-staff-ai

## Purpose

Produce a comprehensive, rated assessment of every agent, skill, and key capability in the project. Each item is scored on three dimensions (1-10):

- **General usefulness** — How valuable is this capability for an SMCR staff officer?
- **Out-of-box capability** — How well does it work right now with zero user customization?
- **User-tuned capability** — How well could it work with profile data, module packs, handoff notes, and configuration?

The output is a visual heatmap widget plus a written gap analysis with prioritized improvement recommendations.

## When to Use

- After major agent or skill changes (enrichment, consolidation, new additions)
- Periodic health checks (monthly or quarterly)
- Before planning the next development sprint
- When asked "how good are our agents" or "what needs work"

## Workflow

### Step 1 — Inventory all capabilities

Read the live state from the codebase. Do not rely on memory or prior assessments.

#### Agents

```bash
# Get the full agent roster from registry
grep -A 200 'def default_agents' app/services/agents/registry.py | head -100
```

```bash
# Get agent IDs and names
grep -rn 'id="' app/services/agents/ --include="*.py" -h | grep -v test | grep -v '#'
```

#### Skills

```bash
# List all project skills
ls .claude/skills/
```

```bash
# Get skill names and descriptions
grep -r 'name:\|description:' .claude/skills/*/SKILL.md
```

#### Key capabilities to also assess

Beyond individual agents and skills, rate these cross-cutting capabilities:

- **Echelon modifier system** — how well do staff archetypes adapt across company/battalion/regiment/division?
- **Source reference coverage** — how well do citations cover the doctrinal landscape?
- **Staff Council deliberation** — how useful is multi-archetype vetting?
- **Custom MOS recipes** — how useful is the user-extensibility model?
- **Module pack system** — how useful is the content-loading mechanism?
- **Session handoff** — how well does continuity survive between sessions?
- **Dashboard UX** — how well does the web UI serve the user?

### Step 2 — Read each capability's current state

For each agent, read its system_prompt, mos_depth, focus, products, and references_extra to assess depth. For skills, read the SKILL.md. Do not guess — read the actual files.

Key files to check:
- `app/services/agents/source_refs.py` — reference coverage per domain
- `app/services/agents/staff_advisor_agent.py` — archetype depth (mos_depth, focus, products)
- Each standalone agent file — system_prompt richness
- Each skill SKILL.md — completeness and actionability

### Step 3 — Score each capability

Rate each item 1-10 on the three dimensions. Use these anchors:

| Score | Meaning |
|-------|---------|
| 1-2 | Stub or placeholder — barely functional |
| 3-4 | Basic structure exists but lacks domain depth |
| 5-6 | Workable but generic — a knowledgeable user would need to fill gaps |
| 7-8 | Good depth — provides real value with minimal user effort |
| 9-10 | Excellent — domain-expert-level guidance, well-cited, actionable |

Scoring guidelines:
- **General usefulness**: Would an SMCR company or battalion staff officer actually use this? How often? For what?
- **Out-of-box**: Does the system prompt contain enough doctrine, process knowledge, and templates to produce useful output without any user configuration? Are references cited? Are products listed?
- **User-tuned**: If the user fills in their profile (billet, unit, MOS), loads module packs, and maintains handoff notes, how much better does this get?

### Step 4 — Build the visual output

Use the `show_widget` tool to render an interactive heatmap. The widget should:

1. Show all capabilities in rows grouped by category (Standalone Agents, Staff Archetypes, Skills, Cross-cutting)
2. Three color-coded columns for the three dimensions
3. Color scale: red (1-3) → amber (4-6) → green (7-10)
4. Sort by average score ascending (weakest first) to prioritize gaps
5. Show the overall average for each dimension at the top
6. Include a filter to show only items below a threshold (e.g., "show items scoring < 5 on out-of-box")

### Step 5 — Gap analysis

After the visual, write a structured gap analysis:

```markdown
## Gap Analysis

### Critical gaps (any dimension < 4)
- [item]: [which dimension is weak] — [what's missing] — [specific fix]

### Improvement opportunities (any dimension 4-6)
- [item]: [which dimension could improve] — [what would move the score]

### Strengths (all dimensions >= 7)
- [item]: [why it scores well]

### Top 5 highest-ROI improvements
Ranked by: (potential score gain) × (general usefulness score)
1. [item] — [change] — [expected score movement]
2. ...

### Enrichment prompt suggestions
For any item scoring < 5 on out-of-box, suggest a specific deep-research prompt
that would fill the gap (same format used for the 7 research reports that fed
the current enrichment round).
```

## Comparison mode

If a prior assessment exists (check for `docs/capability-assessment-*.md` or ask the user), show score deltas with arrows (↑↓→) to track improvement over time.

## Output artifacts

After presenting the visual and analysis:

1. **Do NOT save** the full assessment to the main repo (it would be gitignored anyway)
2. Offer to save a timestamped snapshot to `smcr-staff-ai-personal/docs/capability-assessment-YYYY-MM-DD.md` if the user wants to track progress over time
3. The visual widget is ephemeral — it lives in the conversation only

## Rules

- Read every file before scoring. Do not rate from memory.
- Be honest. Inflated scores defeat the purpose.
- Distinguish "useful but shallow" (high usefulness, low out-of-box) from "deep but niche" (low usefulness, high out-of-box).
- Security constraint: do not include any classified, CUI, or sensitive information in the assessment output.
- The assessment itself is UNCLASSIFIED and safe to share.
