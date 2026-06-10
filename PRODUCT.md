# PRODUCT.md

Context file for `impeccable` and design-aware skills.
Keep this updated as the product evolves.

---

## What This Is

A local-first advisory toolkit for Selected Marine Corps Reserve (SMCR) staff officers.
It runs entirely on the user's machine. No cloud dependency, no SaaS subscription.

The product has two surfaces:
1. **Dashboard** — `http://localhost:8000/dashboard` — a single-page browser app
2. **API** — `http://localhost:8000/docs` — FastAPI backend for direct route access

---

## Who Uses It

**Primary user:** An SMCR officer — O2 through O5 — managing reserve obligations between monthly drill weekends with limited staff support and significant administrative friction.

**Their context:**
- Works a civilian job. The reserve is a second job, not a full-time one.
- Limited time between drills. Tasks pile up silently.
- Frequently covers multiple staff lanes alone (thin staff problem).
- Friction sources: DTS, MROWS, RIDT, FitRep deadlines, PME requirements, MARADMIN tracking, billet awareness.
- Not necessarily a power user. Technically comfortable enough to run a local server but not a developer.

**Secondary user:** A unit S-6, admin chief, or battalion staff officer using it as a planning and product-drafting aid.

---

## What It Does

Turns scattered reserve obligations, source updates, notes, and working context into:
- Prioritized daily/drill-period action briefs
- Staff product scaffolds (WARNO, OPORD, FRAGO, AAR, etc.)
- Admin workflow drafts (DTS, MROWS, RIDT, FitRep, award packages)
- Training planning packages
- Source monitoring (MARADMINs, NAVADMINs, reading list)

Every output is advisory. Human review required. Nothing is authoritative.

---

## Design Language

**The product is a quiet tool for serious work.**

Not a consumer app. Not a polished SaaS product. Not a toy.
Think: a well-organized field desk. Clean, purposeful, no wasted space.

### Color and tone
- Dark by default (`--bg: #090b0d`, `--surface: #12161b`)
- Scarlet accent (`#b21f2d`) used sparingly — command panel border, error states, critical severity
- Amber (`#b4892f`) for warnings and staleness signals
- All other color is muted grey (`--muted: #aab4bf`, `--text: #eef2f6`)
- No decorative gradients, no shadows for aesthetics, no rounded-corner excess

### Typography
- Interface: Inter / Segoe UI sans-serif
- Functional text hierarchy: h1 1.4rem → h2 1.4rem → h3 1rem → body 0.94rem → meta 0.82-0.88rem
- Labels are uppercase, small, heavy (`strip-label` pattern)
- Data is left-aligned, readable, not styled for impressiveness

### Layout
- Grid-based (`summary-grid`, `two-column`, `three-column`) — no absolute positioning tricks
- Panels have consistent `18px` padding, `6px` radius, `1px solid var(--line)` borders
- Content collapses behind `<details>` drawers — user controls what's expanded
- Density: tight but not cramped. Every element earns its space.

### Interaction
- Actions are always explicit (buttons, not hover tricks)
- The lane navigation is tab-based — Overview / Watch / Bench+Files / Workflows / Workspace
- Tool outputs appear inline below the form that triggered them
- Floating `<dialog>` for quick-launch tools (Lone Planner, Staff Package)
- No animations except `behavior: smooth` scroll — nothing for its own sake

---

## Anti-Patterns — What This Is NOT

- **Not a consumer app.** No onboarding carousels, no confetti, no gamification.
- **Not a polished SaaS product.** No marketing copy in the UI. No "Get started for free!"
- **Not a generic AI chatbot.** No chat interface. Structured inputs produce structured outputs.
- **Not visually loud.** The work is serious. The UI should step back and let the content lead.
- **Not decorative.** Every visual element must serve a functional purpose.
- **Not generic AI slop.** No gradient hero banners. No card-grid "features" pages. No hollow visual metaphors.

---

## Key Constraints

- Vanilla JS only (no framework, no build step) — the dashboard is a single HTML file + CSS + JS
- Dark mode only — no light mode toggle
- Must work offline after initial load (no CDN dependencies)
- Accessible: WCAG AA contrast, keyboard navigable, screen reader friendly
- No external fonts — Inter loaded from system or `font-family` stack fallback

---

## Current State (as of 2026-06-03)

**Dashboard lanes:** Overview (Act Now + readiness + source watch) / Watch / Bench+Files / Workflows / Workspace

**Skill layer:** 9 operator skills covering chief brief, monitoring, meeting→actions, source trust, connector normalization, briefings, handoff

**API surface:** 39+ routes across planning, training, staff, admin, career, actions, ingestion

**Known gaps:**
- Some empty states are functional but not helpful (just say "nothing here" with no guidance)
- Error states show raw API error text — not human-readable
- First-run experience improved but not complete
- Tool output rendering is consistent but plain — no visual hierarchy within outputs
