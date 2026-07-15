# Readiness and Leader Development Suite Design

**Date:** 2026-07-15

**Status:** Approved

**Scope:** Travel/GTCC, FitRep analytics, Chief of Staff capabilities, leader development agents, unit fitness planning, financial readiness, and local professional-reference libraries.

## Purpose

Extend SMCR Staff AI from a collection of staff utilities into a cohesive local-first personal and unit-readiness system. The suite reduces administrative friction, helps users deliberately improve as leaders, and lets the Chief of Staff agent coordinate existing app capabilities without receiving unrestricted operating-system access.

The design preserves the dashboard improvements already delivered on `main`: desktop launch, independent feed refresh actions, RSS/source-update dates, Demo-mode filtering, working templates, the top-level FitReps lane, visible agent IDs, FitRep-linked initial counseling, and the CRT EGA browser icon.

## Global Constraints

- UNCLASSIFIED information only.
- User state remains local and user-key scoped under the configured SMCR Staff AI state directory.
- No runtime cloud dependency is introduced. Existing preview-and-approval rules continue to govern optional external inference.
- Every generated advisory or staff product includes: `DRAFT — Verify all references against current official sources before acting.`
- No agent diagnoses illness or injury, determines official body-composition status, provides individualized investment/tax/legal advice, impersonates a credentialed professional, or accepts official risk for a commander.
- Avoid unnecessary PII. Fitness limitations are represented as aggregate planning constraints, not named medical details.
- Built-in source content is committed to the repository. User documents, receipts, financial entries, FitRep records, and custom cadences remain local and are not committed.
- Official web links and stored references are starting points. The UI displays source titles, verification dates, and reminders to confirm the current publication or local SOP.

## Information Architecture

### Workspace

Workspace keeps its existing operational panels and gains a third first-class panel named **Travel**. Travel is a user-driven record, not a bank feed. The panel visibly states when it was last updated and warns that it may be stale.

### FitReps

The existing top-level FitReps lane remains the home for report continuity, counseling relationships, personal profile uploads, Reporting Senior profile uploads, manual entries, and analytics.

### AI

New or expanded agents appear in the existing categories:

- **Reserve Admin & Readiness:** GTCC Advisor, Financial Readiness Advisor, Fitness Planning Advisor.
- **Command & Leadership:** Leadership Advisor and Warrior-Monk.

Stable agent IDs are displayed on every card.

## Travel and GTCC

### Unified trip and ledger model

A travel event owns:

- title, purpose, destination, start/end dates, and status;
- optional DTS authorization/voucher references without credentials;
- linked receipt documents stored through the existing local document/context capabilities;
- ledger entries with transaction date, merchant/description, amount, category, payment responsibility, notes, and optional receipt link;
- card-check records with checked date, optional statement balance, optional payment amount/date, paid-in-full state, notes, and source marked as user-entered;
- created/updated timestamps.

Users may create a trip manually, attach existing receipts, upload new receipts, add or edit ledger entries, and mark a balance check complete. A trip summary shows total logged spend, user-entered payments, possible outstanding amount, missing receipt links, and last user update. Calculations are explicitly estimates based only on entered data.

### Monthly GTCC check

The application surfaces a monthly reminder until the user records a check for the current month. Every reminder provides:

1. **Open CitiManager** — direct link to the official CitiManager sign-in page.
2. **Open Travel tracker** — navigates to the Workspace Travel panel.
3. **Mark checked** — opens a short form for date, optional balance/payment information, and notes.

The reminder never claims the actual bank balance is known. The Chief of Staff brief may surface stale trips, unlinked receipts, unresolved user-entered balances, and the monthly check reminder.

### GTCC Advisor

The GTCC Advisor is narrowly scoped to official travel-card friction:

- CitiManager access and troubleshooting context;
- card activation/declines and program-role escalation prompts;
- split-disbursement and voucher follow-up awareness;
- delinquency-prevention checklists;
- linking users into the Travel panel and official resources.

It does not become a personal-finance advisor and does not store credentials, full card numbers, or bank exports.

## FitRep Profiles and Analytics

### Data entry

FitReps accepts three equally supported input paths:

1. **Upload My Record** — a user-provided report history/profile document is uploaded locally, parsed into proposed records, and shown in a review screen before saving.
2. **Upload RS Profile** — a user-provided Reporting Senior profile is uploaded locally, parsed into proposed profile snapshots, and shown for review before saving.
3. **Manual entry** — the user can add or correct the same fields directly.

Imports must never silently overwrite existing records. Parsed values retain document provenance and confidence/uncertainty notes. Unsupported or ambiguous fields remain blank for user review.

### Personal report model

Each report may include:

- reporting period and occasion;
- grade, billet, unit, Reporting Senior identity label, and Reviewing Officer identity label;
- trait values when available;
- relative value, cumulative relative value, comparative assessment, and profile context when available;
- accomplishments, counseling links, development observations, and private notes;
- source type, source document ID, and created/updated timestamps.

### Reporting Senior snapshots

An RS profile snapshot stores the profile label, effective/as-of date, grade population, report counts, attribute/relative-value data supplied by the user, and source provenance. Snapshots are append-only history by default so trends remain auditable.

### Analytics

The dashboard computes transparent descriptive analytics only from user-entered or user-confirmed data:

- relative-value trend across reports;
- average and range by Reporting Senior;
- trait trend by reporting period;
- comparative-assessment distribution;
- report frequency and observed-profile sample size;
- improvement goals and evidence under one selected Reporting Senior;
- data-quality panel explaining missing fields and small-sample limitations.

Charts must show exact underlying values in accessible tables or labels. They do not predict promotion, selection, or future Reporting Senior marks. The coaching language focuses on observable performance, documentation quality, counseling, and goal follow-through rather than gaming a profile.

### Counseling relationship

The existing Initial Counseling feature remains separate from a FitRep but may link to one Marine/report record. FitReps shows linked counseling drafts and can open or create them directly. The new analytics may reference counseling goals and follow-up evidence without copying the counseling draft into an official report.

## Chief of Staff Capability Gateway

The Chief of Staff is the user-facing coordinator for the application, not a raw filesystem shell.

### Read capabilities

It may read user-key-scoped information exposed through typed application services, including:

- profile and handoff data;
- tracked actions and reminders;
- Workspace notes and projects;
- Travel trips, ledger summaries, receipts metadata, and card-check history;
- FitRep records, RS profiles, analytics, and counseling links;
- agent catalog, locally stored source metadata, and generated products.

Repository source and documentation may be searched through a read-only, repository-root-scoped capability. Excluded paths include secrets, environment files, VCS internals, local credential stores, caches, and arbitrary locations outside the repository and configured user-state roots.

### Write capabilities

- Explicit requests such as “add this GTCC entry” or “save this FitRep record” may append data through the domain API and return an Undo action.
- Inferred document imports produce a proposed change set and require review before persistence.
- Edits that replace existing values show the previous and proposed values.
- Delete, bulk replacement, external transmission, or movement of files requires explicit confirmation.
- Agent responses describe what was read or changed and identify the affected domain record.

The first implementation supports approved domain operations instead of a generic arbitrary-write tool.

## Agent Architecture

### Leadership Advisor

The existing stable `leadership-advisor` ID remains. Its scope expands into the practical Marine Leader Development hub:

- the six functional areas: Fidelity, Fighter, Fitness, Family, Finance, and Future;
- self-assessment, goals, counseling, coaching, command climate, and leader-development plans;
- routing specialized questions to Fitness, Financial Readiness, GTCC, SEL/SgtMaj, or other staff agents;
- Family remains within the MLD framework and does not receive a standalone agent.

MLD check-ins are developmental records and are not performance evaluations.

### Warrior-Monk

`warrior-monk` is a separate philosophical and reflective advisor sharing leadership sources but not task ownership. Its voice is austere, candid, humble, and grounded in Marine warfighting philosophy and public-domain Stoic texts. It supports reflection on fidelity, discipline, courage, responsibility, mortality, meaning, and conduct.

It does not impersonate General James Mattis, fabricate quotations, act as clergy or a mental-health professional, or replace legal/medical/religious support. When reflection produces an actionable development objective, it offers a handoff to Leadership Advisor.

### Financial Readiness Advisor

`financial-readiness-advisor` remains deliberately separate from GTCC. It covers:

- reading and checking an LES/myPay information architecture;
- budgeting, emergency savings, debt awareness, and military consumer protections;
- TSP concepts and official educational resources;
- preparation for a Personal Financial Manager/Counselor conversation.

It does not recommend specific securities, provide tax/legal determinations, access accounts, or store account/routing numbers. A GTCC question is handed to the GTCC Advisor; a travel-card balance is never folded into personal-finance analytics without an explicit user choice.

### Fitness Planning Advisor

`fitness-planning-advisor` supports individual and unit programming while clearly presenting itself as planning support rather than a credentialed Force Fitness Instructor.

Inputs include objective, Marine count from 5 through 50, session/cycle duration, ability-group constraints, PFT/CFT focus, equipment, location, environmental constraints, leader/monitor availability, aggregate limitations, and cadence preference.

The local planning defaults are:

- 5–12 Marines: one group, pairs, or a single circuit;
- 13–24 Marines: two ability groups or rotating stations;
- 25–50 Marines: platoon-style stations with assistant leaders, accountability checks, and staggered movement.

These bands are application heuristics, not doctrine, and remain editable.

Outputs include objectives, timeline, stations/exercises, volume/intensity/rest, ability scaling, equipment, facilities, hydration, leader assignments, accountability, warm-up/cooldown, recovery, environmental controls, emergency actions, cadence block, and an ORM matrix.

### Staff-integrated PT review

A structured `UnitPtPlan` is used for all handoffs:

1. Fitness Planning Advisor creates the draft program.
2. S-3/OpsO reviews objective, scheduling, sequencing, conflicts, and commander’s intent.
3. S-4 reviews equipment, facilities, transportation, hydration, and support.
4. SgtMaj/SEL reviews accountability, standards, scaling, leader coverage, morale, and cadence suitability.
5. ORM reviews hazards, initial risk, controls, control owners, residual risk, no-go criteria, and stop-training authority.
6. Fitness Planning Advisor synthesizes one final executable plan.

The existing scenario-chain schema is extended with typed Fitness, OpsO, SEL, and ORM outputs rather than relying on unvalidated prose. The ORM product is a planning matrix and does not represent formal commander risk acceptance.

## Creeds, Oaths, and Cadences

### Built-in sources

The repository stores source-attributed, verification-dated local references for:

- NCO Creed;
- SNCO Creed;
- Oath of Office;
- Oath of Enlistment;
- a command-safe cadence library containing official/public-domain material or new traditional-style text that can legally be redistributed.

The source index and relevant agent reference packs link these files. Leadership Advisor, Warrior-Monk, SEL/SgtMaj, and Fitness Planning Advisor may retrieve them.

### User cadence library

Users may create, edit, delete, tag, and export private cadence entries. Fields include title, call, response, pace, activity type, tags, content rating, source type, and notes.

Built-in cadences default to command-safe. User entries may be tagged `clean`, `traditional`, `user-provided`, or `adult`. Adult/bawdy output is opt-in for the current request and never inserted automatically into a unit plan. Mild non-graphic adult humor or profanity may be supported; slurs, targeted degradation, hazing, harassment, sexual violence, or attacks on protected groups are rejected.

When building unit PT, the Fitness Planning Advisor asks:

- whether cadences should be included;
- run/march/activity and pace;
- built-in, saved-personal, or newly drafted source;
- command-safe or explicitly requested adult tone.

User-provided copyrighted text may remain private user content but is not redistributed in the built-in library.

## Source Baseline

Primary baseline sources, verified for this design on 2026-07-15:

- Marine Leader Development: <https://www.usmcu.edu/Academic-Programs/Lejeune-Leadership-Institute/Marine-Leader-Development/>
- MCO 6100.13A w/ Admin Ch-5: <https://www.marines.mil/Portals/1/Publications/MCO%206100.13A%20W%20ADMIN%20CH-5%20%28SECURED%29.pdf>
- MCO 6110.3A w/ Admin Ch-4: <https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2863863/mco-61103a-wadmin-ch-4/>
- Force Fitness Instructor Program: <https://www.tbs.marines.mil/MAFCE/Force-Fitness-Instructor-Program/>
- Marine Corps body-composition standards portal: <https://www.fitness.marines.mil/BCP_Standards/>
- DoD Financial Readiness Network: <https://finred.usalearning.gov/About>
- Military OneSource personal finance: <https://www.militaryonesource.mil/financial-legal/personal-finance/>
- DFAS myPay information: <https://www.dfas.mil/mypayinfo/>
- Thrift Savings Plan: <https://www.tsp.gov/>
- NCO/SNCO creeds, MCWP 6-11 Part 4: <https://www.marines.mil/Portals/1/MCWP%206-11_Part4.pdf>
- Oath of Office, 5 U.S.C. § 3331: <https://uscode.house.gov/view.xhtml?req=%28title%3A5+section%3A3331+edition%3Aprelim%29>
- Oath of Enlistment, 10 U.S.C. § 502: <https://uscode.house.gov/view.xhtml?req=%28title%3A10+section%3A502+edition%3Aprelim%29>

Source dates and current-version status must be confirmed again during implementation before exact policy claims are added.

## Error, Empty, and Stale States

- Every list provides a useful empty state and a direct create/upload action.
- Failed uploads preserve the local file and explain which fields could not be parsed.
- A partial import is reviewable and does not save automatically.
- User-driven financial, GTCC, and FitRep data displays last-updated timestamps.
- Missing linked receipts or deleted linked records do not delete the parent trip/report.
- Agent handoff failures return the completed reviews and identify the missing review rather than discarding the plan.
- Demo mode uses explicitly demo-tagged fixtures; turning Demo off immediately removes them from all new surfaces while preserving real user records.

## Accessibility and Cohesion

- All new controls are keyboard reachable and use visible focus states.
- Forms have persistent labels, validation text, and status announcements.
- Charts have text/table equivalents and do not encode meaning by color alone.
- Per-row asynchronous actions expose pending, success, and failure states without blocking unrelated rows.
- Links that leave the application are labeled as external.
- Existing dashboard typography, spacing, card language, and navigation conventions are reused.
- The final pass validates desktop launch, favicon, feeds, source updates, Demo filtering, templates, FitReps/counseling, AI IDs, and all new features together.

## Testing and Release

Each subsystem receives schema/store/service/route tests and dashboard bundle assertions. High-value browser flows cover:

- creating a trip, adding a ledger entry, linking a receipt, and marking the monthly GTCC check;
- importing and reviewing FitRep/RS data, adding a manual record, reading analytics, and following a counseling link;
- asking the Chief of Staff to read and explicitly append supported domain data while confirming protected changes;
- generating a 5-Marine and a 50-Marine PT plan, completing staff reviews, and producing the ORM matrix;
- creating and retrieving a private cadence and confirming adult content remains opt-in;
- locating all new agent IDs and official-source links.

Before merge, run:

```text
uv run pytest tests/ -q
uv run mypy app tests
uv run ruff check .
```

Then perform a browser cohesion review and fix discovered regressions before committing, pushing, and merging through GitHub.

DRAFT — Verify all references against current official sources before acting.
