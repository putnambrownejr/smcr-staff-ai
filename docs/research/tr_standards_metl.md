# T&R Standards, METs, and METLs — Research Report

*Research completed 2026-06-13. Sources verified. All content UNCLASSIFIED.*

---

## 1. Authoritative Sources

### NAVMC 3500 Series

The NAVMC 3500 series is the primary authoritative source for all USMC T&R standards. Published by TECOM, maintained in the **Marine Corps Publications Electronic Library (MCPEL)**:
- https://www.marines.mil/News/Publications/MCPEL/Tag/87635/tr-manual/

**Distribution A (publicly available) examples:**
- NAVMC 3500.3E — Manpower and Administration
- NAVMC 3500.18D — Marine Corps Common Skills Vol 1
- NAVMC 3500.27B — Logistics (LOG)
- NAVMC 3500.44D — Infantry (most recent)
- NAVMC 3500.56 — Communications
- NAVMC 3500.100A/C — Intelligence

Some editions are marked "Secured" (FOUO/CAC-required). Distribution A titles carry "DISTRIBUTION STATEMENT A — approved for public release."

PDF download pattern: `https://www.marines.mil/Portals/1/Publications/NAVMC%203500.XXX.pdf` (CDN returns 403 to bots; accessible via browser with standard request headers)

### Governing Doctrine

| Document | Title |
|---|---|
| MCTP 7-20A | Unit Training Guide (current) |
| MCO 1553.3A/B | Unit Training Management (UTM) |
| MCRP 7-20A.1 | Training Plan Design |
| MCRP 7-20A.4 | Evaluations and Assessments |
| MCRP 7-20A.5 | Training Data Management |
| MCO 3000.13B | Force Readiness Reporting (DRRS-MC) |
| MCO 1553.10 | MCTIMS policy order |

### MCTIMS

MCTIMS is the authoritative CAC-authenticated system for all MET/METL management.
- **Task Master module**: Authoritative Data Source for all Marine Corps Tasks (MCTs) and approved METs/METLs
- **UTM module**: Where units publish METLs, plan training schedules, record completions, and generate readiness assessments
- Training data automatically transfers to DRRS-MC and MCTFS
- No public API — all access requires CAC authentication
- Modernization effort (MCTIMS 2.0) underway as of 2026

---

## 2. Data Model

### Hierarchy

```
MCTL (Marine Corps Task List)
  └── MCT (Marine Corps Task)           ← dictionary entry, organized by Warfighting Function
        └── MET (Mission Essential Task) ← commander selects from MCTL
              └── METL (Mission Essential Task List) ← unit's approved set of METs
                    └── T&R Events       ← training events that train/evaluate each MET
                          └── E-Coded Events ← subset used to calculate CRP
```

### Six Warfighting Functions (WFFs)
1. Maneuver
2. Intelligence
3. Fires
4. Logistics
5. Command and Control
6. Force Protection

### MCT Numbering

Hierarchical decimal: `MCT [WFF#].[sub#].[sub-sub#]`

Examples:
- `MCT 1.6.1` — Conduct Offensive Operations
- `MCT 1.6.4` — Conduct Defensive Operations
- `MCT 4.3` — Conduct Transportation Operations
- `MCT 5.1.1` — Provide and Maintain Communications

### MET Fields (in MCTIMS Task Master)

| Field | Description |
|---|---|
| MCT Number | e.g., MCT 1.6.1 |
| Task Title | Short name |
| Warfighting Function | One of six WFFs |
| Conditions | Operational environment, equipment provided, cues |
| Standard | Proficiency statement for acceptable performance |
| Supporting Tasks | Lower-level MCTs that enable the MET |
| Supported Higher Task | Parent MCT |

### T&R Event Structure

**Event code format:** `4-4-4 alphanumeric` (e.g., `INF-AMPH-8001`)
- Field 1: Community/MOS (e.g., `INF`, `LOG`, `0311`)
- Field 2: Functional area (e.g., `AMPH`, `C2`, `LOG`, `FP`)
- Field 3: Level + sequence number (8000 series = Regimental; lower = individual/crew/unit)

**T&R Event Fields:**

| Field | Description |
|---|---|
| Event Code | 4-4-4 identifier |
| Event Title | Behavioral name |
| Evaluation-Coded (E) | Yes/No — whether this event counts toward CRP |
| Sustainment Interval | Months before retraining required |
| Supported MET(s) | MCT numbers this event supports |
| Conditions | Environment, resources provided |
| Standard | Acceptable proficiency level |
| Performance Steps | Numbered required actions |
| References | Governing doctrinal publications |
| Prerequisite Events | Other T&R events that must be done first |
| Support Requirements | Range, simulators, OpFor needed |

### Combat Readiness Percentage (CRP)

- MET CRP = completed E-Coded events ÷ total required E-Coded events for that MET
- Unit CRP = average across all METs
- CRP feeds into DRRS-MC via MCTIMS automatically

---

## 3. Reserve-Specific Nuances

### Training Time Constraints

- 48 drill periods/year = 24 battle assemblies (one weekend/month)
- 14 days Annual Training (AT) per year
- Functional METL training time per battle assembly: **~8–12 hours** after mandatory training, admin, PT, muster

**AT is disproportionately valuable** — often the only time to run collective T&R events. Many E-Coded collective events have 6–12 month sustainment intervals aligned with once-yearly AT.

### METL Requirements (same policy as active component)

- Commander must submit METL within 30 days of assuming command or 15 days of new mission assignment
- Annual review required
- SMCR METLs typically have fewer METs than active-duty, reflecting training time constraints

### T/P/U Rating System

| Rating | Meaning |
|---|---|
| **T** — Trained | Can perform to standard; sustainment only needed |
| **P** — Practiced | Can perform with shortcomings; refresher required |
| **U** — Untrained | Cannot perform to standard |

The T/P/U rating is a **commander's subjective assessment** informed by MCTIMS CRP data, subordinate input, and evaluations — not auto-generated. Very few SMCR units achieve full T-ratings given training time constraints.

### Current Operational Context (2026)

Marine Corps Reserve Command is planning its first major mobilization exercises since the 1980s, beginning no later than Q4 FY2026. This is reshaping SMCR training priorities — speed to deploy and METL readiness are being re-weighted.

---

## 4. High-Value Integration Targets (Pain Points)

### Pain Point 1: Post-Drill MCTIMS Data Entry
After each battle assembly, the S-3 manually logs training event completions in MCTIMS UTM — linking events to 4-4-4 codes, marking Marines trained. Delayed by armory network access issues and competing civilian employment.

**Opportunity:** Pre-populate a training log from the published drill schedule; auto-suggest T&R event codes from plain-language description; batch-submit completions.

### Pain Point 2: METL Status Brief Preparation
Preparing the CO's METL brief requires pulling CRP data per MET, cross-referencing sustainment interval countdowns, applying T/P/U judgment, and formatting a product. Currently a manual spreadsheet/slide-deck exercise.

**Opportunity:** Auto-generate METL status brief from MCTIMS-exported CRP data; flag METs at risk of P→U transition based on sustainment countdown.

### Pain Point 3: Long-Range Training Plan (LRTP) Writing
Annual LRTP maps METs to available training events across drill weekends and AT. Writing it requires cross-referencing E-coded event requirements against the training calendar while deconflicting mandatory training.

**Opportunity:** Given approved METs and E-coded requirements, generate a draft LRTP that schedules events across the drill year, flagging unsatisfiable constraints.

### Pain Point 4: Mandatory Training Deconfliction
A significant portion of every battle assembly is consumed by ancillary mandatory training (tracked in MCTIMS IMM and MarineNet), competing with METL-focused training time.

**Opportunity:** At planning time, calculate remaining METL training hours after mandatory requirements are mapped to the drill schedule.

---

## 5. Data Availability Assessment

| Data Element | Source | Format | Access |
|---|---|---|---|
| MCT/MET definitions | MCTIMS Task Master | Database | CAC only |
| T&R event structure | NAVMC 3500 PDFs | PDF (parseable) | Public (Distribution A) |
| Unit METL (approved) | MCTIMS UTM | Database / manual entry | CAC only; export possible |
| Training event completions | MCTIMS UTM | Exportable report | CAC only |
| CRP per MET | MCTIMS calculated | Report export | CAC only |
| T/P/U ratings | Commander's assessment | Manual input | N/A |
| Sustainment interval countdowns | NAVMC 3500 PDFs + last-trained date | Calculated | Derive from PDF + date |

### Recommended Integration Path

1. **Phase 1 — Manual METL entry**: User enters their unit's approved METs as structured data in the dashboard
2. **Phase 2 — NAVMC 3500 PDF ingestion**: Parse Distribution A PDFs for relevant occupational fields; extract T&R event tables as structured JSON
3. **Phase 3 — MCTIMS export import**: User exports training completion report from MCTIMS; dashboard ingests it as the live data layer

All three phases are achievable with publicly available data and no CAC-gated dependencies.

---

*Sources: MCPEL NAVMC 3500 listings, MCO 1553.3A/B, MCTP 7-20A, MCRP 7-20A series, MCO 3000.13B, DRRS-MC Commanders Readiness Handbook 2020, MCTIMS modernization MARADMIN, Defense News (2025-04-29), GlobalSecurity USMC MCRP 3-0A.*
