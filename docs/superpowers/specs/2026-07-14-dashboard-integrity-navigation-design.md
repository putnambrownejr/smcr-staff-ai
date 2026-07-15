# Dashboard Integrity and Navigation Design

Date: 2026-07-14  
Status: Approved design; pending implementation plan

## Objective

Finish the approved dashboard cleanup as one coordinated pass: make Watch feeds
truthful and independently refreshable, keep demo content out of real mode,
make every template link resolve to a real template, promote FitReps to a
top-level page, expose stable agent identifiers, and use the CRT EGA artwork for
the browser and desktop small icons.

This work remains local-first. It does not add cloud inference, background web
crawling beyond the existing feed refresh services, or destructive cleanup of
project folders.

## 1. Connected Feeds and Source Updates

### Connected-feed actions

Each row on Watch receives one action based on the source capability:

- MARADMIN: **Refresh**, calling the existing MARADMIN refresh endpoint.
- NAVADMIN: **Refresh**, calling the existing NAVADMIN refresh endpoint.
- Real custom RSS/Atom feed: **Refresh**, calling that feed's existing refresh
  endpoint.
- Static webpage such as Marine Corps Gazette: **Open source**, opening its
  configured URL.
- Manual unit feed: **Manual**, shown disabled because there is no automated
  source to call.

Each automated row owns its own transient state: idle, refreshing, success, or
failure. Refreshing one row must not disable unrelated rows. The existing global
refresh remains available and continues to refresh all automated sources.

### RSS dates

The dashboard carries `published_at` from ingested message records through the
dashboard ticker/feed response. When supplied by the upstream feed, the UI shows
the publication date. When absent, the UI omits the date; it must not invent one
or substitute retrieval time without labeling it.

The existing RSS parser already reads published/updated timestamps into
`FeedItem.published_at` (`app/services/ingestion/rss_client.py`). Stored message
records already distinguish `published_at` and `retrieved_at`
(`app/schemas/message_watch.py`).

### Real Source Updates

Remove the two hardcoded dashboard examples. The Source Updates panel loads the
real backend candidates produced by `DocumentUpdateMonitor`, which scans message
records for possible changes to tracked publications
(`app/services/ingestion/document_update_monitor.py`).

Add an optional `source_published_at` field to each update candidate. The
monitor copies the triggering message's `published_at` when available. The UI
shows:

- **Published** followed by `source_published_at`, when present.
- **Detected** followed by the existing `detected_at`, otherwise.

Detection remains advisory: these records indicate a possible source change,
not confirmation that policy or doctrine changed.

### Failure behavior

Refresh failures remain scoped to the affected row and show a short useful
message. Previously loaded content stays visible. A partially failed global
refresh reports which sources failed without discarding successful results.

## 2. Demo-Mode Isolation

### Personal files

When Demo mode turns off, immediately clear demo-derived Personal files and
Project files from frontend state before loading the real user's workspace. The
Personal files card remains visible and then shows either the real user's files
or its existing empty state.

A failed or slow real-user request must never leave demo filenames visible.
Turning Demo mode back on reloads the demo-scoped records through the existing
demo seed flow.

### Demo project metadata

Project visibility must use explicit metadata, never a folder-name heuristic.
Introduce a `.smcr-project.json` sidecar inside a project folder. It can
represent at least:

```json
{
  "name": "repo-maintenance",
  "is_demo": true
}
```

Create that sidecar in the existing local `projects/repo-maintenance` folder and
mark it as demo. The project-listing API returns structured project descriptors
including `is_demo`. A missing sidecar defaults to `is_demo: false`; invalid
metadata is reported as non-demo rather than hiding user work. Demo mode may show
demo projects; real mode filters them out immediately.

Turning Demo mode off does **not** delete `repo-maintenance` or any of its files.
Only explicitly flagged folders are hidden. A similarly named unflagged project
must remain visible.

## 3. Template Library Integrity

The seed catalog currently describes 49 system templates but points the UI at
fragments in the YAML catalog rather than individual usable files
(`data/seed/system_templates.example.yaml`).

Create one checked-in Markdown scaffold for every system-template record under
a dedicated template directory. Each scaffold includes the template title,
purpose/instructions, the catalog's headings, and the required draft-verification
footer. Add the real source path to the catalog/API response and make each
Template Library entry open that file through the existing safe reveal route.

Validation enforces one-to-one coverage:

- every catalog record has exactly one existing template file;
- every generated system-template file maps to a catalog record;
- IDs and source paths are unique;
- dashboard references no longer target YAML fragments.

Markdown is the canonical format for this pass. Generating DOCX copies is out of
scope because the request is to make the library links resolve to actual,
editable templates.

## 4. FitReps as a Top-Level Page

Add **FitReps** as a top-level dashboard tab beside Workspace, placed between
Workspace and AI. Move the complete FitRep Tracker section out of Workspace into
the new page without duplicating it.

The new page reuses the existing FitRep state, filters, archive/delete controls,
autosave behavior, and `/user-docs/fitreps` persistence. Existing saved reports
remain compatible because there is no storage-schema change
(`app/api/routes/user_docs.py`, `app/schemas/user_docs.py`).

Update internal quick links so “FitRep Tracker” opens the FitReps tab. Workspace
then contains only Logbook and Session / Drill Handoff. The layout remains
responsive: the report list and editor may use two columns at desktop widths and
stack at narrow widths.

## 5. Stable Agent IDs on the AI Page

Every agent card shows its stable registry ID directly below or beside the
human-readable name, for example:

```text
Planning Advisor (MCPP / R2P2 / OPT)
Agent ID: planning-advisor
```

Use `AgentMetadata.id`, which the `/agents` API already returns and the
dashboard card mapping already carries (`app/schemas/agents.py`,
`app/api/routes/agents.py`). Do not expose Python filenames: multiple virtual
staff agents share `staff_advisor_agent.py`, so filenames are not a stable
one-agent-to-one-file identifier.

The ID is always visible, styled as secondary monospace text, and remains usable
for copying into prompts, API calls, or issue reports.

## 6. CRT EGA Browser and Desktop Icons

The current generator deliberately substitutes a procedural chevron for the
16x16 and 32x32 variants (`scripts/generate_app_icon.py`). Replace those small
variants with a contrast-enhanced crop of the CRT screen containing the EGA.

Keep the full CRT artwork for 192x192, 256x256, and 512x512 variants. Use the
cropped EGA screen for 16x16, 32x32, and 48x48 variants so browser tabs and small
Explorer/taskbar surfaces remain legible.

Regenerate all checked-in icon assets from
`scripts/assets/crt-icon-source.png`. Append `?v=crt-ega-1` to the injected
favicon URLs so Chrome and Firefox do not keep displaying a cached chevron. The
PWA manifest and desktop ICO continue to reference the same identity family.

## Architecture and Change Boundaries

Follow the existing compiled-dashboard workflow: durable dashboard changes are
expressed through `scripts/patch_dashboard_bundle.py`, then applied to
`app/static/dashboard/index.html`. Do not hand-edit generated icon files; update
and run `scripts/generate_app_icon.py`.

Backend changes are limited to:

- exposing feed/update publication timestamps already present in source records;
- returning real Source Updates data;
- returning structured project descriptors with an explicit demo flag;
- returning real template source paths.

No unrelated agent behavior, doctrine content, authentication, or storage-home
rules change in this pass.

## Verification

Automated coverage will include:

- per-feed action mapping and independent row status;
- publication-date presence and omission behavior;
- real Source Updates replacing hardcoded examples and Published/Detected label
  selection;
- immediate demo-state clearing and real-user empty-state behavior;
- explicit demo project filtering without deletion or name-based filtering;
- exact template catalog/file coverage and resolvable reveal paths;
- FitReps tab navigation, Workspace removal, and existing FitRep CRUD behavior;
- visible agent IDs for every rendered agent;
- served favicon/PWA assets and deterministic icon regeneration.

Run the dashboard-focused tests first, then the complete test suite, Ruff, and
MyPy. Finally, open the local dashboard in a browser and verify Watch, Demo mode,
Template Library, FitReps, AI agent cards, and the browser-tab icon. Because
favicons are aggressively cached, browser verification must use the new icon URL
or a fresh profile/tab.

## Accepted Decisions

The user approved all of the following on 2026-07-14:

1. Static/non-automated feeds open their source page; manual feeds show Manual.
2. Use real Source Updates and show publication dates when available.
3. Keep the Personal files card and show only real-user files or an empty state.
4. Create and link every missing system template.
5. Preserve `repo-maintenance` on disk while hiding it outside Demo mode.
6. Promote FitReps to a top-level tab beside Workspace.
7. Show stable agent IDs, not source filenames.
8. Use the cropped CRT EGA for browser and other small icon variants.
