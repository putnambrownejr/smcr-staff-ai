# Skill Catalog

Packaged repo-local skills for humans and connected AI tools.

## Available Skills

- `important-staff-docs`
  - Use when building, reviewing, or routing Marine staff products such as WARNOs, OPORDs, FRAGOs, SITREPs, running estimates, CUBs, CPBs, AARs, annexes, appendices, and correspondence.

- `chief-brief-ops`
  - Use when turning commitments, blockers, local handoffs, action items, and stored context into a Chief of Staff / Aide style daily or drill-period brief.

- `meeting-to-action`
  - Use when converting meeting notes, transcripts, or rough notes into decisions, due-outs, action items, and a follow-up draft.

- `usmc-monitoring`
  - Use when monitoring MARADMINs, public-source updates, readiness requirements, and reserve-relevant changes without drifting into unsupported interpretation.

- `handoff`
  - Use at the end of a session to write a structured handoff document so a fresh agent or new session can continue without re-reading conversation history.

- `pptx`
  - Use when creating, editing, or extracting content from PowerPoint (.pptx) files — decision briefs, back-briefs, AARs, CUBs, and MDMP slide packages.

- `source-trust-review`
  - Use when reviewing the freshness and verification status of doctrine or policy sources. Routes follow-up work based on trust state: verified-current, needs-review, or update-detected.

- `personal-chief-of-staff`
  - Use when you need a single integrated brief covering handoff state, open actions, career watch, admin due-outs, and drill prep in one pass. Extends chief-brief-ops across the full personal admin and continuity surface.

- `connector-adapter`
  - Use when normalizing external calendar, email, or travel summaries into repo-native schemas and workflow paths. Bridges outside inputs to local routes without the repo owning OAuth.

- `frontend-design`
  - Use when building web components, pages, dashboards, or any UI for the SMCR staff app. Enforces distinctive, production-grade aesthetics and avoids generic AI output patterns.

- `systematic-debugging`
  - Use when diagnosing non-trivial bugs across any component of the app. Blocks fixes until root cause is confirmed; forces architectural review after three failed attempts.

- `brainstorming`
  - Use before any feature or component work. Hard-gated: no code until a design is presented and approved. Proposes 2-3 approaches, writes a spec doc, then hands off to writing-plans.

- `grill-me`
  - Use before implementing any non-trivial feature or data model change. One-question-at-a-time design review that produces a numbered decision log before any code is touched.

- `grill-with-docs`
  - Use when existing CONTEXT.md or ADRs exist in the repo. Anchors the design review to recorded decisions, challenges terminology against the domain model, and updates docs inline.

## Working Rule

Prefer existing repo routes, services, schemas, and local storage workflows before inventing new logic. These skills are operating overlays, not replacements for the app's core behavior.
