---
name: capability-router
description: Route a task to the right agent, skill, or execution mode within smcr-staff-ai before work begins. Use at the start of non-trivial tasks, when the user asks which agent covers a topic, or when a task spans multiple staff lanes.
---

# Capability Router — smcr-staff-ai

## Purpose

Choose the right agent, skill, or execution path before starting work in this project. Keep the routing pass small and biased toward action.

## When to Route Visibly

- The task may need a specific agent from the 35-agent registry.
- The task spans multiple staff lanes (e.g., logistics + operations + legal).
- The user asks "which agent handles X" or "who should I ask about Y."
- The work touches the Staff Council (multi-agent deliberation).
- The task involves a custom MOS recipe or echelon-specific advice.

For simple, obvious requests (single lane, clear agent), make the routing decision silently and proceed.

## Agent Registry — Quick Reference

### Standalone Agents (19)

| Agent ID | Lane |
|---|---|
| chief-of-staff | CoS coordination, continuity, turnover |
| leadership-advisor | PME, command climate, historical perspective |
| planning-advisor | MCPP / R2P2 / OPT deliberate & rapid planning |
| red-team-assumptions-challenge | Pressure-test plans, assumptions challenge |
| assessment-learning-advisor | AAR linkage, assessment cycle |
| writing-briefing-coach | Staff writing, command briefs |
| infantry-tactics-advisor | 03XX infantry training, familiarization |
| fires-advisor | Fire support, artillery, mortars, NSFS, CAS |
| installation-practical-advisor | Base access, visitor control |
| uniform-advisor | Uniform regs, grooming, inspection prep |
| drill-prep-calendar | Drill reminders, recurring calendar events |
| orm-risk-management | ORM, safety, risk worksheets |
| staff-products | Staff product scaffolds (AAR, OPORD, FRAGORD) |
| pki-cac-troubleshooter | CAC/PKI/MarineNet certificate issues |
| osint-research-assistant | Open-source research for training scenarios |
| terrain-map-advisor | Public topo, terrain, map products |
| ace | ACE / Air Combat Element coordination |
| gce | GCE / Ground Combat Element maneuver |
| lce | LCE / Logistics Combat Element sustainment |

### Staff Archetypes (16) — prefix `staff-`

staff-xo, staff-battle_captain, staff-opso, staff-s1, staff-s2, staff-s4, staff-s6, staff-sel, staff-surgeon, staff-sja, staff-pao, staff-chaplain, staff-provost, staff-ig, staff-g8, staff-g9

All staff archetypes support **echelon modifiers**: battalion, regiment, division_group. Pass via `context.extra.echelon`.

### Staff Council

The Staff Council (`/api/staff-council/{user_key}`) runs a multi-agent deliberation across all 16 staff archetypes. Use it when:
- The problem genuinely spans 3+ staff lanes.
- The user wants a "full staff estimate" or "council of war."
- Cross-staff risks and coordination notes matter.

Do NOT route to the council for single-lane questions — use the specific agent.

### Custom MOS Recipes

Users can create custom MOS advisor recipes that extend any parent agent with MOS-specific focus areas. Check `/api/custom-mos-recipes/{user_key}` if the user mentions a specific MOS code.

## Routing Workflow

1. Classify the task by domain, staff lane, and echelon.
2. Identify the primary agent. If one clearly fits, route there.
3. Identify supporting agents only if cross-lane coordination genuinely helps.
4. Decide: single agent, Staff Council, or direct execution (no agent needed).
5. If the task is a dev/engineering task on the codebase itself, skip agent routing — handle directly.

## Output (when visible)

- **Primary**: agent ID and name
- **Supporting**: optional secondary agents, if cross-lane
- **Mode**: single agent / Staff Council / direct / custom MOS recipe
- **Why**: one sentence
- **Echelon**: battalion / regiment / division_group (if applicable)

## Security Constraint

All routing outputs are UNCLASSIFIED advisory drafts. Do not route tasks that require classified information, CUI, COMSEC, real frequencies, call signs, or precise unit movements. Flag and decline.
