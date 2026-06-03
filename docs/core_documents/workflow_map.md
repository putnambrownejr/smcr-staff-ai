# Workflow Map

How routes combine into real operating flows. Use this as the entry point for understanding
what the system actually does, not just what endpoints exist.

---

## Flow 1 — Daily Readiness Check

*"What needs my attention right now?"*

```
GET /chief/brief/{user_key}
  → surfaces: action_items, next_drill_readiness, handoff_is_stale flag,
              admin_watch, career_watch, battle_rhythm_health

GET /career/watch/{user_key}
  → surfaces: fitrep_watch, pme_watch, tracked_opportunities

GET /actions?user_key={key}
  → surfaces: open POAMs, blocked items, waiting-on

Dashboard aggregates all three → Act Now panel
```

Demo path (no auth): `GET /demo/chief/brief` + `GET /demo/career/watch`

---

## Flow 2 — Meeting Notes → Action Items

*"I just came out of a sync. What are the due-outs?"*

```
POST /analysis/summarize
  body: { text: "<raw meeting notes>", ... }
  → structured summary with key decisions and open questions

POST /actions/track
  body: { title, owner, suspense_date, category, user_key }
  → stores individual due-out in the action tracker

POST /staff-products/poam
  body: { title, facts, guidance_items, ... }
  → full POAM scaffold from the meeting output
```

Skill overlay: `meeting-to-action`

---

## Flow 3 — Source Update → Brief → Due-Outs

*"A new MARADMIN just dropped. Does it affect my unit?"*

```
POST /maradmins/refresh
  → pulls latest feed items into local storage

GET /maradmins/feed
  → returns recent items with Reserve-relevance tags

POST /analysis/summarize
  body: { text: "<MARADMIN text>", source_context: "maradmin" }
  → summary with affected population, dates, action items

POST /actions/track  (if action required)
  → stores follow-up as a tracked due-out
```

Skill overlay: `usmc-monitoring`

---

## Flow 4 — Drill Prep Package

*"Drill is in two weeks. What's the staff package?"*

```
POST /planning/staff-package
  body: { title, event_type, mission_or_training_goal,
          coordinating_sections, constraints, ... }
  → XO sync, command cell, S-1/Admin, Safety, SEL,
    Medical, and staff product scaffolds in one pass

POST /training/planning-cell  (for S-3 lane)
  body: { title, mission_or_training_goal, ... }
  → mission analysis, planning approach, assumption log,
    decision log, due-outs

POST /staff/safety-plan  (for Safety/ORM lane)
POST /staff/medical-plan  (for Medical lane)
POST /staff/s1-readiness  (for S-1/Admin lane)
```

Skill overlay: `chief-brief-ops`

---

## Flow 5 — Handoff → Resume

*"I'm picking this up after two weeks away."*

```
GET /handoffs/{user_key}
  → retrieves stored session handoff

GET /chief/brief/{user_key}
  → builds a fresh brief using the handoff as context,
    flags handoff_is_stale if > 14 days old

GET /career/watch/{user_key}
  → surfaces any PME, FitRep, or opportunity changes

GET /actions?user_key={key}
  → shows what was open when you left
```

Skill overlay: `handoff` (writes the outgoing doc), `chief-brief-ops` (reads the incoming state)

---

## Flow 6 — Travel / Admin Claim

*"My DTS voucher was denied. What do I do?"*

```
POST /staff/s1/dts-helper
  body: { title, facts, constraints }
  → DTS authorization scaffold and review checklist

POST /staff/s1/mrows-rebuttal
  body: { title, facts, constraints }
  → MROWS denial rebuttal with JTR 020204 citation and documentation checklist

POST /staff/s1/ridt
  body: { title, facts, constraints }
  → RIDT scaffold with reason codes, documentation checklist,
    commander endorsement reminder
```

---

## Flow 7 — Billet Search

*"I want to find an open billet that fits my MOS and location."*

```
POST /billets/recommend
  body: { mos, rank, desired_locations, keywords, willing_to_travel }
  → scored billet recommendations from the public BIC

GET /billets/scrape  (refreshes the local billet cache)
```

---

## Full Route Inventory

For every available endpoint: `http://localhost:8000/docs`
For agent catalog: `docs/agents_setup/AGENTS.md`
For demo/stateless versions: any `/demo/*` route
