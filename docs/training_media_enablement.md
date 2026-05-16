# Training Media Enablement

These notes summarize the locally ingested MP4 use-case demos currently stored in local context. They are based on file names, durations, and local metadata only. They are not transcript-derived yet.

The ingested media remains:

- local-only
- advisory
- non-canonical
- excluded from doctrine, org, and source manifests

## Ingested Media

| File | Duration | Likely focus |
| --- | --- | --- |
| `uc_01_maj_garcia_shortcut_dashboard.mp4` | `00:09:51` | shortcut-driven dashboard / daily staff cockpit |
| `uc_02_data_merging.mp4` | `00:04:20` | merging multiple data sources into one working picture |
| `uc_03_cgip_fac_assistant.mp4` | `00:04:56` | CGIP / FAC advisory assistant workflow |
| `uc_04_capt_bowden_ai_coding.mp4` | `00:03:54` | AI coding or automation helper workflow |
| `uc_05_drafting_professional_emails.mp4` | `00:05:23` | email drafting and correspondence support |
| `uc_06_tdg_generator.mp4` | `00:03:25` | tactical decision game generator |
| `uc_07_msgt_mcclure_apex.mp4` | `00:02:32` | APEX or admin-planning assistant workflow |
| `uc_08_capt_goff_poam.mp4` | `00:01:41` | POAM drafting / maintenance workflow |

## Highest-Value Enablement Ideas

### 1. Use-Case Library

Add a first-class "use-case library" view that treats these videos like training references:

- title
- short synopsis
- tags
- linked routes or agents
- example prompt
- related doctrine or admin references
- local file context ID

This would make the media useful even before full transcript support exists.

### 2. Transcript Pipeline

Add an optional local transcript workflow for media stored in the user-scoped local-context store (outside the repo by default, or inside the Docker volume when containerized):

- detect `video/*` and `audio/*`
- extract audio track
- run speech-to-text locally or through a user-approved model path
- store transcript as a sibling local-context text item
- extract timestamps, key actions, route mentions, and named capabilities

This is the most important next step if we want the videos to become searchable by meaning.

### 3. Capability Crosswalk

For each video, create a crosswalk between:

- demonstrated workflow
- existing API routes
- missing backend pieces
- missing UI pieces
- needed connectors
- needed agent upgrades

That turns each clip into a build backlog item instead of just reference media.

### 4. "Show Me How" Mode

Build a route that returns:

- what the feature does
- what data it needs
- what agent/route powers it
- what the user would click or ask
- what is stubbed versus implemented

This would let ChatGPT or the dashboard answer: "show me the POAM workflow" or "show me the email drafting workflow."

### 5. Workflow Templates

Each video likely maps to a reusable template bundle:

- dashboard checklist template
- data merge template
- FAC / inspection checklist template
- email drafting template
- TDG scenario template
- POAM template

Those can be stored as structured JSON/YAML prompt packs or response scaffolds.

## Suggested Mapping To Current Repo

### Shortcut Dashboard

Likely maps to:

- `/chief/brief/{user_key}`
- `/admin/readiness/{user_key}`
- `/career/watch/{user_key}`
- `/dashboard`

Best next enhancement:

- personalized dashboard sections
- pinned cards
- saved drill views
- one-click daily/weekly reserve triage

### Data Merging

Likely maps to:

- `/analysis/summarize`
- local context uploads
- staff products
- future spreadsheet merge helpers

Best next enhancement:

- merge multiple uploads into one synthesized summary
- extract action items by source
- deconflict overlapping dates, names, and due-outs

### CGIP / FAC Assistant

Likely maps to:

- inspection prep checklists
- admin workflows
- staff products
- future source/document verification

Best next enhancement:

- FAC / inspection packet builder
- evidence tracker
- corrective-action watchlist

### AI Coding

Likely maps to:

- automation ideas
- Codex / repo development workflows
- future "build me a helper" workflows for Marines

Best next enhancement:

- prompt-to-utility workflow suggestions
- small script template library

### Drafting Professional Emails

Likely maps to:

- correspondence-formatting agent
- staff products
- future email connector workflows

Best next enhancement:

- professional tone presets
- military email pattern library
- review mode for clarity, tone, and action requests

### TDG Generator

Likely maps to:

- training workflows
- staff products
- leadership / PME support

Best next enhancement:

- TDG generator route
- difficulty levels
- MOS or echelon-specific injects
- discussion guide and facilitator notes

### APEX

Likely maps to:

- admin workflows
- planning checklists
- future connector/state synchronization

Best next enhancement:

- structured planning worksheet
- progress tracker
- routing and suspense views

### POAM

Likely maps to:

- staff products
- admin workflows
- dashboard action tracking

Best next enhancement:

- POAM schema
- owner / suspense / status tracking
- export to slide or CSV-ready format

## Definition Of "Enabled"

For these media use cases, "enabled" should probably mean five layers:

1. the media is stored and indexed locally
2. the workflow has a written synopsis and example prompt
3. the workflow maps to at least one real route or agent
4. the dashboard can surface and launch it
5. transcripts or structured notes make it searchable

Right now we have layers `1` and part of `3`.

## Recommended Next Build

The best next implementation would be a `use-case catalog` with:

- local training media listing
- synopsis field
- linked routes
- status: `idea`, `scaffolded`, `working`, `stubbed`
- example prompt
- related files and doctrine refs

That would let these videos actively shape the product instead of just sitting in local storage.
