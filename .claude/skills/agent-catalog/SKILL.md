---
name: agent-catalog
description: Print the current smcr-staff-ai agent roster with IDs, names, and types (standalone / staff archetype / MAGTF element). Use when asked "what agents exist", "show the roster", "agent catalog", or after a consolidation round to confirm the final count.
---

# Agent Catalog — smcr-staff-ai

## Purpose

Print a current, verified agent roster by reading the live registry — not from memory or a stale list. Use this after consolidation rounds, when onboarding, or whenever the agent count or IDs are in question.

## How to Generate

### Step 1 — Read the registry

```bash
# Get all agent builder functions called in default_agents()
grep -A 200 'def default_agents' app/services/agents/registry.py | head -80
```

### Step 2 — Extract IDs and names from each agent file

```bash
# Get agent ID and name from every agent builder
grep -rn 'id="' app/services/agents/ --include="*.py" -h | grep -v test | grep -v '#'
grep -rn 'name="' app/services/agents/ --include="*.py" -h | grep -v test | grep -v '#'
```

### Step 3 — Classify and format

Organize agents into three categories based on their ID pattern and location:

#### Standalone Agents
Agents with unique IDs (no `staff-` prefix) that are NOT MAGTF elements. These are specialized advisors for specific domains.

#### Staff Archetypes
Agents with the `staff-{role}` ID pattern. These represent traditional staff section roles and support echelon modifiers (battalion, regiment, division_group). All 16 participate in Staff Council deliberation.

#### MAGTF Element Agents
The three MAGTF warfighting element agents: `ace`, `gce`, `lce`. These are standalone (not in the Staff Council) but represent organizational elements rather than staff functions.

## Output Format

```markdown
# Agent Catalog — <date> — <total count> agents

## Standalone Agents (<count>)

| ID | Name |
|---|---|
| chief-of-staff | Chief of Staff |
| planning-advisor | Planning Advisor |
| ... | ... |

## Staff Archetypes (<count>) — all support echelon modifiers

| ID | Name |
|---|---|
| staff-xo | XO / Executive Officer |
| staff-opso | OpsO / S-3 |
| ... | ... |

## MAGTF Elements (<count>)

| ID | Name |
|---|---|
| ace | ACE / Air Combat Element |
| gce | GCE / Ground Combat Element |
| lce | LCE / Logistics Combat Element |

---
Total: <N> agents (<standalone> standalone + <archetypes> staff archetypes + <magtf> MAGTF elements)

Staff Council routes to: <archetype count> staff archetypes
Custom MOS recipes can extend: <count from VALID_PARENT_AGENTS>
```

## Verification

After generating the catalog, cross-check:

```bash
# Count registered agents at runtime
python -c "from app.services.agents.registry import AgentRegistry; print(len(AgentRegistry().list_metadata()))"
```

The runtime count must match the catalog count. If it doesn't, an agent file exists but isn't imported in `registry.py`, or vice versa.

## Related

- **capability-router** — uses this roster to route tasks to the right agent
- **find-skills** — searches this roster when users ask "which agent handles X"
- **custom MOS recipes** — `VALID_PARENT_AGENTS` in `app/api/routes/custom_mos_recipes.py` controls which agents can parent recipes
