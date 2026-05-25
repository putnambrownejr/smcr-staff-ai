# Staff Products Quick Reference

This note is a compact resource map for staff-product agents. It is not a copy of doctrine and should not be treated as an authoritative order template.

## Official References

- MCWP 5-10 Marine Corps Planning Process
  - Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900553/mcwp-5-10/
  - Use for MCPP, orders development, staff estimates, R2P2, and transition discipline.

- MCDP 5 Planning
  - Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899841/mcdp-5/
  - Use for planning philosophy, uncertainty, commander decision support, and deliberate versus rapid planning.

- MCTP 3-30A Command and Staff Actions
  - Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/
  - Use for command-post rhythm, staff-action flow, estimates, briefs, and cross-staff coordination.

- CJCSM 3150.05F Joint Reporting System Situation Monitoring Manual
  - Official URL: https://www.jcs.mil/Portals/36/Documents/Library/Manuals/CJCSM%203150.05F.pdf
  - Use for SITREP and operational-report framing when a joint-style report model is needed.

- MCO 1553.3C Unit Training Management
  - Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899431/mco-15533c/
  - Use for standards-based training, evaluation, and AAR discipline.

- SECNAV M-5216.5 and MCO 5216.20B
  - Official URLs:
    - https://www.secnav.navy.mil/doni/SECNAV%20Manuals1/5216.5%20%20CH-1.pdf
    - https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2795618/mco-521620b-wadmin-ch-4/
  - Use for naval correspondence, memoranda, endorsements, routing, and formal package formatting.

## Critical Product Mockups

### WARNO

```text
1. Situation: what changed or may change.
2. Mission/task: likely task, purpose, and timeframe.
3. Initial tasks: immediate prep by unit or staff section.
4. Timeline: planning events, suspenses, next update, decision point.
5. Coordinating instructions: RFIs, constraints, required products, POCs.
```

### OPORD / CONOP

```text
1. Situation: enemy/threat, friendly, attachments, terrain/weather, civil considerations.
2. Mission: who, what, when, where, why.
3. Execution: intent, concept, tasks, coordinating instructions, assessment.
4. Sustainment: supply, movement, maintenance, medical, personnel/admin.
5. Command and Signal: command relationships, CPs, succession, reports, PACE.
```

### FRAGO

```text
Reference: base order and serial.
Changes: only what changed.
Tasks: updated task/purpose by unit or staff section.
Coordinating instructions: timing, control measures, reports, constraints.
Unchanged: what remains in effect from the base order.
```

### SITREP

```text
Current status:
Operations:
Personnel/casualties:
Logistics/equipment:
Communications/C2:
Significant events:
Next 24-72 hours:
Decisions or support required:
```

### Running Estimate

```text
Section:
Current situation:
Changes since last update:
Assumptions:
Risks:
Supportability:
Asks of adjacent sections:
Decisions needed:
Next 24-72 hours:
```

### CUB

```text
Executive snapshot:
Main effort status:
Changes since last brief:
Top friction:
Commander decisions required:
Support requests:
Due-outs and owners:
```

### CPB - Civil Preparation of the Battlespace

Use only for Civil Affairs/G-9 planning. Do not use CPB as a generic commander planning brief.

```text
Civil frame:
ASCOPE factors:
Civil actors:
Civil information gaps:
Civil risks:
Effects on the scheme:
Recommended CA actions:
Coordination required:
```

### AAR

```text
Event and standard:
What was supposed to happen:
What actually happened:
Sustains:
Improves:
Root friction:
Corrective action, owner, suspense:
Next event/rehearsal to verify:
```

## Role To Product Map

| Role | Products |
| --- | --- |
| Commander/XO | Guidance, decision brief, transition brief, approval/signature |
| S-3/G-3/OpsO | WARNO, OPORD, FRAGO, CONOP, Annex C, synchronization matrix |
| S-2/G-2 | Intelligence estimate, Annex B, PIR/IR list, IPB notes |
| S-4/G-4/LCE | Logistics estimate, Annex F, movement table, sustainment matrix |
| S-6/G-6 | Signal/communications plan, PACE matrix, information-management checks |
| Surgeon/Doc | Medical estimate, casualty plan, CASEVAC/MEDEVAC checks |
| AirO/ACE | Air support estimate, air-ground coordination matrix, airspace/control questions |
| SJA | Legal issue spotter, ROE/RUF guardrails, legal review trigger list |
| PAO/COMMSTRAT/G-7 | Public affairs plan, release matrix, themes/messages, OPSEC review |
| G-9/CA | Civil Preparation of the Battlespace, civil affairs/civil considerations annex, partner coordination, ASCOPE notes |
| Safety | ORM worksheet, no-go criteria, residual-risk acceptance note |
| Provost | Security annex, access-control plan, traffic/force-protection checks |
| Chaplain/RP | Religious support plan, RMT logistics, morale/confidentiality boundary note |
| IG | Inspection/inquiry boundary note, readiness trend memo |

## Agent Usage

- `staff-products`: choose the product scaffold and citations.
- `staff council`: return role-specific recommended products and source citations.
- `s3-opso`, `mcpp-planning-assistant`, `r2p2-planning-assistant`: enforce planning rhythm and transition discipline.
- `s2-intel`, `s4-logistics`, `s6-comms`, `medical-doc-advisor`, `airo-advisor`, `jag-legal-advisor`, `g9-civil-military`: provide section-specific estimate and annex inputs.

Keep outputs advisory, source-cited, and training-safe unless the user provides an approved environment and confirms the work is appropriate for that environment.
