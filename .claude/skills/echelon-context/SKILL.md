---
name: echelon-context
description: Detect echelon from user prompts and explain how it changes agent behavior. Auto-sets the echelon modifier (platoon through division/group) when routing to staff archetype agents, so the user doesn't have to remember to pass it explicitly.
---

# Echelon Context — smcr-staff-ai

## Purpose

Bridge the gap between how users naturally describe their scenario ("my battalion S-4", "the division G-3 wants…", "at the regimental level") and the echelon modifier system built into the staff archetype agents. This skill detects echelon signals, sets the right context, and explains what changes.

## When to Use

- When routing any task to a staff archetype agent (`staff-*` pattern)
- When the user mentions a unit type, staff prefix, or organizational level
- When the user asks "what changes at division level" or "how does this differ for a battalion"
- When comparing how the same agent responds across echelons
- When the user's profile has an echelon set but the current prompt implies a different one

## Echelon Detection

Scan the user's prompt for these signals and map to the right `StaffEchelon` value:

### Platoon (`platoon`)

**Signals:** "platoon", "plt", "platoon sergeant", "platoon commander", "squad"

**What changes:** Minimal staff structure. Most staff functions handled by the platoon commander and platoon sergeant directly. Agents focus on immediate tactical concerns, not formal staff products.

### Company (`company`)

**Signals:** "company", "co", "battery", "btry", "troop", "company commander", "1stSgt", "company XO", "company gunnery sergeant"

**What changes:** Limited organic staff. XO doubles as primary staff officer. Focus shifts to company-level SOPs, readiness reporting up to battalion, and maintenance/supply at the lowest formal level.

### Battalion (`battalion`) — DEFAULT

**Signals:** "battalion", "bn", "squadron" (ground), "S-1", "S-2", "S-3", "S-4", "S-6", "battalion commander", "SgtMaj", "XO"

**What changes:** Full S-staff structure. Staff prefix is "S-". Products are battalion-level (training plans, LOGSTATs, PERSTATs). This is the default echelon — if no signal is detected, assume battalion.

**Staff behavior at this echelon:**
- S-1: DTS, awards, FitReps, unit diary
- S-3/OpsO: Training plans, range scheduling, drill coordination
- S-4: Tactical logistics, maintenance, supply
- S-6: Tactical comms, PACE plans

### Regiment / MEU / Wing (`regiment_meu_wing`)

**Signals:** "regiment", "regt", "RCT", "MEU", "wing", "MAW", "MLG", "group", "regimental", "MEU commander", "regimental commander"

**What changes:** Staff prefix stays "S-" but scope expands. More formal coordination requirements. Products include regimental-level estimates, MEU-specific planning (ARG/MEU integration), wing-level air tasking. Staff sections have more depth (assistant S-3, future ops cell).

**Staff behavior at this echelon:**
- S-3/OpsO: Synchronization across subordinate battalions, future operations cell
- S-4: Distribution management, MSR/ASR planning
- S-2: Collection management, all-source fusion
- PAO: Media engagement at a level that draws public attention

### Division / Group (`division_group`)

**Signals:** "division", "div", "MEB", "MEF" (route to division as closest supported), "MARFOR", "division commander", "CG", "G-1", "G-2", "G-3", "G-4", "G-6", "G-8", "G-9", "ACofS"

**What changes:** Staff prefix switches from "S-" to "G-". Scope is operational, not tactical. Products are theater-level (OPLANs, force deployment plans, strategic comms). Staff sections are large with multiple cells (current ops, future ops, plans).

**Staff behavior at this echelon:**
- G-3: Operational-level planning, joint/combined coordination
- G-4: Theater logistics, strategic lift, distribution
- G-2: All-source intelligence, national-level coordination
- G-8: Programming and budgeting (not present at battalion)
- G-9: Civil-military operations at scale

## How to Apply

### Step 1 — Detect

Scan the user's prompt for echelon signals from the table above. If multiple signals conflict (e.g., "the battalion within our division"), use the most specific to the task being asked about.

### Step 2 — Confirm or infer

- **Clear signal:** Set echelon and proceed. Mention it briefly: "Setting echelon to regiment_meu_wing based on your mention of the MEU."
- **Ambiguous signal:** Ask one clarifying question: "You mentioned 'the G-3' — are you working at division/group level, or did you mean the S-3?"
- **No signal:** Default to battalion. Don't ask — battalion is the most common SMCR context.

### Step 3 — Route with context

When calling a staff archetype agent, pass the echelon in the context:

```python
context = AgentContext(extra={"echelon": "division_group"})
agent.run(user_prompt, context=context)
```

The agent's `_resolve_echelon()` reads `context.extra["echelon"]` and adapts:
- Staff prefix (S- vs G-)
- Scope language (tactical vs operational)
- Product names (LOGSTAT vs theater logistics estimate)
- Coordination requirements (within-unit vs joint/combined)

### Step 4 — Explain (when helpful)

If the user seems unfamiliar with echelon differences, or asks why an agent responded a certain way, explain what the echelon modifier changed:

"At battalion level, the S-4 focuses on tactical logistics — maintenance readiness, supply requests, field-day supply runs. At division level, the G-4 shifts to theater logistics — strategic lift, distribution networks, and sustainment planning across subordinate units. The same agent, different lens."

## Echelon Comparison Mode

When the user asks "how would this differ at [echelon]" or "compare battalion vs division for this":

1. Run the same prompt through the target agent at both echelons
2. Present a side-by-side comparison highlighting what changed:
   - Staff prefix and title
   - Scope and terminology
   - Products and deliverables
   - Coordination requirements

## Valid Echelon Values

These are the exact string values accepted by `StaffEchelon` in `app/schemas/staff.py`:

| Value | Label |
|---|---|
| `platoon` | Platoon |
| `company` | Company / Battery / Troop |
| `battalion` | Battalion / Squadron (default) |
| `regiment_meu_wing` | Regiment / MEU / Wing / MLG |
| `division_group` | Division / Group / MEB |

## Rules

- **Default to battalion.** Don't ask unless there's a genuine ambiguity.
- **Only applies to staff archetypes.** Standalone agents (fires-advisor, planning-advisor, etc.) and MAGTF elements (ace, gce, lce) don't use echelon modifiers.
- **Don't over-explain.** If the user clearly knows their echelon, just set it and move on.
- **UNCLASSIFIED only.** Echelon context is organizational structure — no unit-specific details, real task org, or deployment information.
