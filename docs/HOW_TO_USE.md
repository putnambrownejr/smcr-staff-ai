# How to Use SMCR Staff AI

This guide is for Marine reserve staff officers and SNCOs who want to understand what this tool does, what it's worth to them, and how to squeeze the most out of it.

---

## What problem does this solve?

Reserve staff work happens in two-hour chunks on a drill weekend, then completely stops for four to six weeks. When you come back, you spend the first hour reconstructing context: what was left undone, who owns what, what's changed in MARADMIN space, where the CO's priorities stand.

SMCR Staff AI is a local command-post dashboard that holds context between duty days so you don't lose it. Most workflows remain entirely local. If an API key is configured, scenario-capable agents can use an external provider only after showing an outbound preview and receiving your explicit acknowledgement.

---

## What's in it for you

**If you're a staff officer (S-1 through S-6):**
- Your section notes, priority stack, and outstanding items are waiting for you when you log in — no "okay so where were we" conversation at the start of drill
- MARADMIN and public watch feeds summarized in one lane so you're not digging through email chains to find the one message that affects your section
- Planning scaffolds for battle rhythm, drill prep, and section products that follow the standard SMCR format

**If you're the XO or Chief of Staff:**
- The chief brief builds from stored section state — readiness posture, must-do items, and blockers in one read
- Stale handoffs surface a visible warning so you know before the brief whether the data you're reading is current
- Act Now queue surfaces items above threshold from across sections, not buried in a long tracker

**If you're the S-3:**
- Workflow launchers for planning cell products
- Drill-prep scaffolding that starts from unit context, not a blank template
- Battle rhythm and timeline tools scoped to reserve drill cycles

---

## The five lanes

### Overview
Your command post. Readiness posture (green / watch / red), Act Now queue, today's history brief, and a command summary built from your loaded workspace. This is what you look at first.

### Watch
Public source feeds — MARADMINs, DoD updates, custom feeds you configure. Reading tracker for PME and assigned material. You don't need to configure ingestion to use the feed summaries; demo mode shows sample data.

### Bench / Files
Your section bench notebook. Configurable dropdown of sections (S-1 through S-6 and others). Notes, references, and context you want surfaced during drill. Uploaded local context files (read-only reference, not executed).

### Workflows
Staff product launchers and planning tools. Thin staff estimate, lone planner, battle rhythm editor, correspondence scaffolds. These produce advisory draft outputs — all require human review before use.

### Workspace
Where you load your personal workspace (or stay in demo mode). This is also where you manage your profile name and passkey. Load personal to unlock all live data; demo mode gives a safe read-only tour.

---

## What this tool does NOT do

**Scope caps — be clear on these before relying on outputs:**

- No classified information. All content is UNCLASSIFIED. Do not enter classified, CUI, COMSEC, sensitive personnel information, real unit call signs, precise movement details, or operational security-sensitive content.
- All outputs are advisory drafts. Nothing this tool produces is authoritative. Products require human review and commander approval before any operational use.
- No real-time data without manual ingestion setup. Feed summaries only populate if you configure ingestion (optional). Out of the box, demo mode shows safe sample data.
- No silent external processing. Normal workflows use templates and stored context. Optional scenario inference shows original and sanitized messages first; choosing either external option requires acknowledgement. Detector findings are warnings, not classification decisions.
- You control disclosure. Choose local template, send sanitized, or send as written. Approval applies only to the displayed operation; changed content requires another review.
- No multi-user sync. This is a single-machine local tool. If you want shared state across a section, you need to export and share files manually.
- No replacement for command judgment. The chief brief, readiness posture, and action priorities are starting points, not finished products.

---

## Getting maximum value

**Routine before drill:**
1. Open the dashboard
2. Check Watch lane — any new MARADMINs that affect your section?
3. Review Act Now — are your open items still accurate?
4. Check the chief brief — does readiness posture still match reality?
5. Update your section bench notes with anything new before the working day starts

**Routine after drill:**
1. Update your section bench notes with the day's outcomes
2. Reload workspace to refresh handoff (Workspace lane → reload)
3. Add or close Act Now items based on what was accomplished
4. Note any blockers or pending items for next drill

**When you're the duty OOD or read file:**
- Watch lane gives you the MARADMIN summary without hunting through email
- Chief brief gives you a one-page snapshot if the CO asks for a quick update
- Bench notebook keeps section-specific context close without switching windows

**For S-3 drill planning:**
- Use battle rhythm tool to block out the drill weekend before it starts
- Run the lone planner workflow to scaffold a training schedule from unit context
- Export the product and clean it up — never submit the raw output

---

## Local notes and uploads are advisory context

Any local files you upload or notes you save are treated as advisory context, not authoritative doctrine. The tool uses your notes to inform outputs — it does not validate them against official sources. Ground truth comes from official publications, unit orders, and command guidance.

---

## Getting help

- [QUICKSTART.md](../QUICKSTART.md) — installation and first-run steps
- [docs/architecture.md](architecture.md) — technical overview for contributors
- Issues and feedback: open a GitHub issue on the repository
