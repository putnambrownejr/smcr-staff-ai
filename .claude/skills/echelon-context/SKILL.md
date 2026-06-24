---
name: echelon-context
description: Detect echelon and MAGTF context from user prompts, auto-set the echelon modifier when routing to staff archetype agents, and explain how echelon changes agent behavior. Understands service echelons (platoon through division), MAGTF packaging (MEU/MEB/MEF/SPMAGTF), task organization, command relationships, and Force Design 2030 implications.
---

# Echelon Context — smcr-staff-ai

## Purpose

Bridge the gap between how users naturally describe their scenario and the echelon modifier system built into the staff archetype agents. This skill detects echelon and MAGTF signals, sets the right context, and explains what changes.

Marine Corps organization uses **two overlapping logics**: relatively stable **service echelons** (squad → platoon → company → battalion → regiment → division) and **task-organized MAGTFs** (MEU, MEB, MEF, SPMAGTF) that combine command, ground, aviation, and logistics elements under one commander. A user saying "my battalion" is using service echelon language. A user saying "my MEU" is describing a MAGTF packaging — which maps to the regiment_meu_wing echelon but carries different context about combined-arms integration and naval employment.

This skill understands both.

## When to Use

- When routing any task to a staff archetype agent (`staff-*` pattern)
- When the user mentions a unit type, staff prefix, organizational level, or MAGTF type
- When the user asks "what changes at division level" or "how does this differ for a MEU"
- When comparing how the same agent responds across echelons
- When the user's profile has an echelon set but the current prompt implies a different one
- When task organization, command relationships, or MAGTF packaging matter to the question

## Key Concept: Echelon ≠ MAGTF Size Class

A **regiment** is a service/ground formation. A **MEU** is a combined-arms expeditionary organization. The Marine Corps deliberately overlays the two:

- A regiment may anchor a **MEB ground combat element**
- A battalion may anchor a **MEU battalion landing team (BLT)**
- A division may form the **GCE of a MEF**

This matters because the same echelon value (`regiment_meu_wing`) produces different agent behavior depending on whether the user is thinking about a regiment in garrison or a MEU deployed on an ARG. When the signal is ambiguous, one clarifying question resolves it.

## Echelon Detection

Scan the user's prompt for these signals and map to the right `StaffEchelon` value:

### Platoon (`platoon`)

**Signals:** "platoon", "plt", "platoon sergeant", "platoon commander", "squad", "fire team", "team leader", "squad leader"

**Typical structure:** 3 rifle squads + platoon HQ (~40 Marines). Squad = 3 fire teams of 4 Marines (13 per squad).

**What changes:** Minimal staff structure. Platoon commander and platoon sergeant handle nearly all functions that a full staff would distribute. No formal staff products. Agents focus on immediate tactical concerns — individual and small-unit tasks, not staff estimates.

**Agent behavior:** Most staff archetype agents will note the limited applicability of their products at this echelon. The value is in tactical planning guidance, not staff process.

### Company (`company`)

**Signals:** "company", "co", "battery", "btry", "troop", "company commander", "1stSgt", "company XO", "company gunnery sergeant", "rifle company", "weapons company", "H&S company"

**Typical structure:** 3 rifle platoons + weapons platoon + HQ platoon (~180–200 Marines for a rifle company).

**What changes:** Limited organic staff. XO doubles as primary staff officer. Focus shifts to company-level SOPs, readiness reporting up to battalion, and maintenance/supply at the lowest formal level. The company is the basic maneuver element of a battalion and can operate semi-independently when reinforced.

**Agent behavior:** Staff agents simplify their products. S-4 focuses on company-level supply and maintenance rather than distribution networks. OpsO focuses on training schedules rather than synchronization matrices.

### Battalion (`battalion`) — DEFAULT

**Signals:** "battalion", "bn", "squadron" (ground), "S-1", "S-2", "S-3", "S-4", "S-6", "battalion commander", "SgtMaj", "XO", "BLT" (Battalion Landing Team), "weapons company", "H&S company"

**Typical structure:** 3 rifle companies + 1 weapons company + 1 H&S company (~900–1,200 Marines). Weapons company adds medium mortars, antiarmor, heavy machine guns. Full S-staff.

**What changes:** This is the first echelon with a complete staff structure. Staff prefix is "S-". Products are battalion-level: training plans, LOGSTATs, PERSTATs, FRAGORDs. The battalion is the fundamental building block — it can serve as a BLT for a MEU, an independent task force, or the GCE of a smaller MAGTF.

**Staff behavior at this echelon:**
- S-1: DTS, awards, FitReps, unit diary, personnel accounting
- S-2: IPB at battalion level, threat assessment for training areas
- S-3/OpsO: Training plans, range scheduling, drill coordination, battalion synchronization
- S-4: Tactical logistics — maintenance readiness, supply requests, class I–IX management
- S-6: Tactical comms, PACE plans, battalion network
- SJA: Issue-spotting, military justice (predominant in garrison)
- Surgeon: CASEVAC planning, training-safe medical support

**Force Design note:** Modernized battalions are receiving loitering munitions, enhanced small UAS, signature-management tools, and EW/SIGINT capability. Battalion-and-below units are expected to be more lethal, more autonomous, and capable of operating with degraded communications.

### Regiment / MEU / Wing (`regiment_meu_wing`)

**Signals:** "regiment", "regt", "RCT", "MEU", "wing", "MAW", "MLG", "MAG", "group", "regimental", "MEU commander", "regimental commander", "CLR", "CLB", "ARG", "amphibious ready group", "MLR" (Marine Littoral Regiment), "SPMAGTF"

**Typical structure:**
- *Regiment:* 3–4 infantry battalions + HQ (~2,500–3,500 Marines, non-reinforced)
- *MEU:* Reinforced infantry battalion (BLT) + composite squadron + CLB + CE (~2,200 Marines). Certified for ~15 days self-sustainment.
- *MLR:* Littoral combat team + littoral anti-air battalion + CLB (~1,800–2,000 Marines). Optimized for EABO, maritime sensing, anti-ship fires.
- *SPMAGTF:* Tailored CE/GCE/ACE/LCE for a specific mission. Size varies.

**What changes:** Staff prefix stays "S-" but scope expands significantly. More formal coordination requirements. Staff sections have more depth (assistant S-3, future ops cell, dedicated collection management). Products include regimental-level estimates, MEU-specific planning (ARG/MEU integration for MEUs), wing-level air tasking (for MAW context).

**Staff behavior at this echelon:**
- S-3/OpsO: Synchronization across subordinate battalions, future operations cell, MAGTF integration
- S-4: Distribution management, MSR/ASR planning, sustainment across multiple battalions
- S-2: Collection management, all-source fusion, CI/HUMINT coordination
- PAO: Media engagement at a level that draws public attention
- SJA: Operational law becomes more prominent alongside military justice
- Surgeon: Health service support across a larger footprint

**MEU-specific context:** When the user mentions a MEU, the agent should understand:
- The MEU is a combined-arms MAGTF, not just a ground formation
- ACE (composite squadron: MV-22B, CH-53, AH-1Z, UH-1Y, F-35B), GCE (BLT), LCE (CLB), CE are all organic
- Employment is sea-based, crisis-response oriented, with ~15-day independent sustainment
- Command relationship involves the ARG/MEU relationship with the Navy (CATF/CLF)

**MLR-specific context:** The Marine Littoral Regiment is not a traditional infantry regiment. It is a stand-in naval formation optimized for expeditionary advanced base operations, maritime sensing, and anti-ship fires (NMESIS). Treat MLR questions as regiment_meu_wing echelon but note the distinct employment concept.

### Division / Group (`division_group`)

**Signals:** "division", "div", "MARDIV", "MEB", "MEF" (map to division as closest supported echelon), "MARFOR", "division commander", "CG", "G-1", "G-2", "G-3", "G-4", "G-6", "G-8", "G-9", "ACofS", "MEF commander", "lieutenant general", "major general"

**Typical structure:**
- *Division:* 3 infantry regiments + artillery regiment + separate combat support battalions (~20,000+ Marines)
- *MEB:* Reinforced infantry regiment + aircraft group(s) + MLG components + CE (~3,000–20,000 Marines). ~30-day sustainment. Can serve as MAGTF or JTF nucleus.
- *MEF:* 1+ Marine divisions + aircraft wings + logistics groups + permanent CE (~45,000–47,000 for I and II MEF). Principal warfighting organization. Deploys by echelon with up to 60 days sustainment.

**What changes:** Staff prefix switches from "S-" to "G-". Scope shifts from tactical to operational. Products are theater-level: OPLANs, force deployment plans, strategic comms. Staff sections are large with multiple cells (current ops, future ops, plans). Command relationships involve joint constructs (COCOM/OPCON/TACON/ADCON).

**Staff behavior at this echelon:**
- G-3: Operational-level planning, joint/combined coordination, synchronization across subordinate regiments/brigades
- G-4: Theater logistics, strategic lift, distribution networks, contested sustainment
- G-2: All-source intelligence, national-level coordination, collection management at scale
- G-8: Programming and budgeting (not present at battalion — unique to this echelon)
- G-9: Civil-military operations at scale, civil reconnaissance, partner engagement
- SJA: Operational and international law dominate; legal support becomes a planning and authorities function
- PAO: Strategic communications, media operations center

**MEF-specific context:** When the user mentions the MEF, understand:
- The MEF is the largest standard MAGTF — it includes divisions, wings, and logistics groups
- MEF (Forward) is a lead echelon that deploys first and prepares for follow-on forces
- MARFOR component commands (MARFORPAC, MARFORCOM, MARFORCENT, etc.) are service components to geographic combatant commanders — not the same as deployable MAGTFs

## Command Relationships

Echelon affects which command relationship vocabulary applies:

| Context | Vocabulary | When to surface |
|---|---|---|
| Within a MAGTF | **Command** and **support** | When the user is discussing internal MAGTF coordination |
| Joint construct | **COCOM / OPCON / TACON / ADCON** | When the user mentions joint operations, combatant commands, or inter-service coordination |
| Amphibious operations | **CATF / CLF** relationship | When the user mentions ARG/MEU ops, amphibious assault, or ship-to-shore movement |

At battalion and below, command relationships are usually straightforward (organic command). At regiment and above, especially in MEU/MEB/MEF contexts, the command relationship architecture must be deliberately designed and is specified in the initiating directive.

## MAGTF Functional Area Mapping

When the user's question involves a specific functional area, the echelon determines which staff section and which level of complexity to apply:

| Functional area | Battalion (S-staff) | Regiment/MEU | Division/MEF (G-staff) |
|---|---|---|---|
| Maneuver/tactics | S-3 — company-level training, range scheduling | S-3 — battalion synchronization, future ops | G-3 — operational planning, joint coordination |
| Fires | S-3 fires — mortars, call for fire | S-3 fires + FSCC — fire support coordination | G-3 fires + FECC — MAGTF-level fires integration, targeting |
| Intelligence | S-2 — IPB, threat assessment | S-2 — collection management, all-source | G-2 — all-source, national-level, CI/HUMINT at scale |
| Logistics | S-4 — maintenance, supply, class I–IX | S-4 — distribution, MSR/ASR | G-4 — theater logistics, strategic lift, contested sustainment |
| Communications | S-6 — battalion network, PACE | S-6 — regimental/MEU networks | G-6 — enterprise networks, MCEN, cyber defense |
| Legal | SJA — military justice (garrison priority) | SJA — operational law surges | SJA — international law, authorities, targeting legal review |
| Medical | Surgeon — CASEVAC, training safety | Surgeon — health service support | Surgeon — medical battalions, theater HSS |
| Civil affairs | Minimal at battalion | G-9/CA — civil reconnaissance, partner engagement | G-9 — CMO at scale, theater civil-military operations |
| Budget/resources | Not applicable | Limited | G-8 — programming, budgeting, resource management |

## Force Design 2030 Implications

When the user's question touches modernization or future operating concepts, note how echelon interacts with Force Design:

- **Battalion and below:** Smaller signatures, more organic sensors (sUAS, EW/SIGINT), loitering munitions, counter-sUAS. Units expected to operate more autonomously with degraded comms.
- **Regiment/MLR:** The MLR is the signature Force Design formation — optimized for EABO, anti-ship fires (NMESIS), maritime sensing. Not a traditional infantry regiment.
- **MEF/Division:** Emphasis on distributed maritime operations, naval integration, contested logistics, joint kill webs. MEFs deploy by echelon rather than as a monolithic force.

When a user asks about a formation in a Force Design context, the agents should emphasize distributed operations, maritime integration, and contested sustainment rather than traditional garrison or legacy employment patterns.

## How to Apply

### Step 1 — Detect

Scan the user's prompt for echelon and MAGTF signals from the tables above. If multiple signals appear:
- **Nested context** ("the battalion within our MEU"): Use the most specific to the task. If they're asking about battalion-level logistics, use battalion. If they're asking about MEU integration, use regiment_meu_wing.
- **Conflicting signals** ("the G-3 at our battalion"): The user may be confused or using informal language. Ask one clarifying question.

### Step 2 — Confirm or infer

- **Clear signal:** Set echelon and proceed. Mention it briefly: "Setting echelon to regiment_meu_wing based on your mention of the MEU."
- **MAGTF signal:** If the user says "MEU" or "MEF", set the echelon AND note the MAGTF context: "Setting echelon to regiment_meu_wing. Since you're in a MEU context, I'll factor in ARG/MEU integration and ~15-day sustainment planning."
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

If the user seems unfamiliar with echelon differences, or asks why an agent responded a certain way, explain what the echelon modifier changed. Use concrete examples:

"At battalion level, the S-4 focuses on tactical logistics — maintenance readiness, supply requests, field-day supply runs. At division level, the G-4 shifts to theater logistics — strategic lift, distribution networks, and sustainment planning across subordinate units. The same agent, different lens."

"In a MEU context, your S-4 isn't just thinking about battalion supply — the CLB handles sustainment for the entire MEU, and logistics planning has to account for sea-based operations, limited ~15-day independent sustainment, and resupply from the ARG."

## Echelon Comparison Mode

When the user asks "how would this differ at [echelon]" or "compare battalion vs division for this":

1. Run the same prompt through the target agent at both echelons
2. Present a side-by-side comparison highlighting:
   - Staff prefix and title (S-4 vs G-4)
   - Scope and terminology (tactical vs operational)
   - Products and deliverables (LOGSTAT vs theater logistics estimate)
   - Coordination requirements (within-unit vs joint/combined)
   - Personnel and capability scale
   - Command relationships
   - Sustainment profile

## Valid Echelon Values

These are the exact string values accepted by `StaffEchelon` in `app/schemas/staff.py`:

| Value | Label | Typical personnel | MAGTF overlay |
|---|---|---|---|
| `platoon` | Platoon | ~40 | N/A |
| `company` | Company / Battery / Troop | ~180–200 | N/A |
| `battalion` | Battalion / Squadron (default) | ~900–1,200 | BLT for MEU |
| `regiment_meu_wing` | Regiment / MEU / Wing / MLG / MLR | ~2,200 (MEU) to ~3,500 (regiment) | MEU, SPMAGTF |
| `division_group` | Division / Group / MEB / MEF | ~20,000+ (division) to ~47,000 (MEF) | MEB, MEF |

## Rules

- **Default to battalion.** Don't ask unless there's a genuine ambiguity.
- **Only applies to staff archetypes.** Standalone agents (fires-advisor, planning-advisor, etc.) and MAGTF elements (ace, gce, lce) don't use echelon modifiers.
- **Don't over-explain.** If the user clearly knows their echelon, just set it and move on.
- **Echelon is context, not classification.** A battalion S-4 in a MEU has different concerns than a battalion S-4 in garrison. Note the MAGTF packaging when it matters.
- **Personnel numbers are typical ranges, not exact T/O&E.** MCRP 1-10.1 explicitly states it no longer contains specific structure information. Use ranges, not false precision.
- **UNCLASSIFIED only.** Echelon context is organizational structure — no unit-specific details, real task org, deployment information, or classified force structure data.
