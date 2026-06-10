# Chat Handoff

Date: 2026-06-04

## Objective

Capture the important context from this chat so work can resume later without reconstructing the thread.

## Current Repo State

- Branch: `main`
- Last known pushed commit from prior session:
  - `b461c0e` - `Add operator skills and repo feedback docs`
- Current uncommitted file at the time of this handoff:
  - `docs/core_documents/dashboard_startup_blocker_2026-06-04.md`

## Prior Work Already In Repo

### Skills added previously

- `skills/README.md`
- `skills/chief-brief-ops/SKILL.md`
- `skills/meeting-to-action/SKILL.md`
- `skills/usmc-monitoring/SKILL.md`

### Docs added previously

- `docs/core_documents/repo_feedback_2026-06-03.md`
- `docs/core_documents/session_handoff_2026-06-03.md`

These were already committed and pushed before this chat segment.

## Main Product Read

Best framing for the repo:

- a local-first SMCR staff copilot
- strongest as a workflow and continuity system, not just a collection of advisory agents
- centered on:
  - awareness
  - readiness / staff sharpness
  - friction reduction for reserve life

Best-fit users:

- individual SMCR officers
- battalion/company staff officers
- XO / Chief / AdminO / S-3 / S-6 type operators
- technically comfortable reservists who want continuity between drill periods

Less suitable users:

- users expecting a polished SaaS app out of the box
- command-authority / official-output workflows
- classified or CUI environments
- users needing full live connector automation today

## Accessibility / Product Direction Read

Main recommendation:

- do not reduce depth
- make the product progressively accessible

Best approach:

- same engine
- better ramp
- fewer discovery and setup barriers

Highest-ROI improvement areas identified:

- first-run / first-15-minutes workflow
- progressive disclosure in the dashboard
- organize around user jobs rather than feature inventory
- more realistic examples and templates
- simpler local setup and contributor quickstart

## Knowledge And Software Requirements Read

Practical usage tiers:

- basic user
  - understands reserve/admin/staff context
  - can review advisory outputs critically
- power user
  - can manage local context and operate structured workflows
- maintainer / builder
  - can work in Python, FastAPI, Pydantic, SQLModel, Git, and local API testing

Software/runtime requirements:

- Python 3.12+
- `venv`
- `pip`
- browser
- terminal
- Git

Important operational constraint:

- local-first
- UNCLASSIFIED-only
- advisory, not authoritative

## User Feedback Items Raised In This Chat

These should be preserved for later product review or backlog work.

### 1. Marine Corps History Facts is empty

Potential paths:

- find how to populate the current feature properly
- or replace/refactor the concept into something like:
  - USMC reference / wiki view
  - random history fact / randomizer

### 2. Section bench notebook lacks an S-2 entry option

Interpretation:

- the current section bench coverage feels incomplete
- S-2 should be available as a first-class entry option

### 3. Section bench notebook should maybe support custom agents

User thought:

- every staff is unique
- users may benefit from choosing and editing their own staff bench

Important note:

- this likely needs more design consideration before implementation
- could be high-value for broader accessibility if done carefully

Key design tension:

- useful customization
- without turning the staff model into a messy free-for-all

### 4. Doctrine / reference library is empty

Idea raised:

- provide doctrine/reference links
- possibly offer optional download behavior

This likely fits the repo well if handled as:

- curated links
- source metadata
- optional local fetch / user-managed download

rather than committing large source files directly

### 5. Commandant's Reading List is empty

Ideas raised:

- add `recommend a book`
- add `other PME`
- allow storage of book reviews and thoughts for later reference

This aligns well with the repo’s continuity and professional-development lanes.

### 6. MOS advisor should be built out further

Specific examples mentioned:

- `0602 communications officer`
- `SJA`
- something stronger for wing / pilots / aviation

Interpretation:

- current MOS / specialty depth is not yet strong enough in some high-value lanes
- this should likely be treated as a capability-depth problem, not only a naming problem

## Dashboard Launch Attempt Summary

You asked to open the dashboard after the earlier link did not work.

### What succeeded

- verified Python is installed
- created `.venv`
- installed repo dependencies successfully with editable install

### What failed

- app did not come up
- `/health` was not reachable
- therefore `/dashboard` never became available

### Why it failed

The blocker appears to be inconsistent runtime path configuration.

Some code paths honor `.env` through `Settings`, but some services still call default path helpers directly, such as:

- `default_local_context_dir()`
- related default storage path helpers

Those direct calls still point to `%LOCALAPPDATA%\smcr-staff-ai` unless `SMCR_STAFF_AI_HOME` is explicitly set in the process environment.

In this workspace, writes outside the repo are restricted, so startup failed before the server could bind.

### Error pattern observed

Startup eventually failed with a permissions error against:

- `C:\Users\PutnamBrowne\AppData\Local\smcr-staff-ai`

Detailed note exists in:

- `docs/core_documents/dashboard_startup_blocker_2026-06-04.md`

## Safe Read On The Blocker

This is not mainly a dashboard bug.

It is a configuration-consistency problem in local runtime storage handling.

Best long-term fix:

- normalize runtime paths through `Settings`
- avoid direct default-path coupling in services that should be configurable

Quick operational workaround:

- ensure local launch scripts set `SMCR_STAFF_AI_HOME` to a repo-local runtime directory

## Suggested Next Actions

### Highest-value engineering follow-up

1. Fix local runtime path consistency.
2. Verify `/health`.
3. Verify `/dashboard`.
4. Only after that, review empty dashboard sections in the running app.

### Highest-value product follow-up

1. Review the empty or thin dashboard lanes:
   - history facts
   - doctrine/reference library
   - reading list
   - section bench notebook
2. Decide which are:
   - data population problems
   - missing route/service problems
   - UX discoverability problems

### Highest-value design/product questions

1. Should section bench remain fixed-role, semi-configurable, or user-defined?
2. Should doctrine/reference be:
   - link catalog only
   - optional local download library
   - indexed local source shelf
3. Should reading support emphasize:
   - official list parity
   - recommendations
   - personal notes/reviews
   - all three

## Recommendation For Resume Point

If work resumes later, the best next step is:

1. resolve the runtime path blocker first
2. get the dashboard actually running
3. then inspect the user-raised empty sections in the live UI

That will separate:

- true missing data
- missing features
- poor discoverability

without guessing from static code alone
