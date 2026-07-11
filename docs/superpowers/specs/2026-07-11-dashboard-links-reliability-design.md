# Dashboard Reliability and Links Directory Design

**Status:** Approved design direction on 2026-07-11
**Implementation target:** `C:\smcr-staff-ai` only
**Publication flow:** Commit and push the project change first, then pull the published commit into `C:\smcr-staff-ai-personal`.

## Problem

The dashboard currently mixes three separate failure classes:

1. Every non-successful HTTP response increments the global connection-failure counter. Expected startup `404` responses can therefore show a false “Connection lost” banner even though the server answered.
2. Both local checkouts default to port `8000`. If one checkout is already running, the other cannot become the server behind the advertised dashboard URL, and the startup path does not explain that clearly.
3. The Links lane renders resources as button-like pills in one long visual stream. Descriptions are hidden in tooltips, compact screens overflow horizontally, request failures are vague or silent, and Links requests omit the configured local passkey.

## Goals

- Show global server-loss warnings only for transport failures, never for ordinary HTTP application responses.
- Make an occupied startup port explicit and allow an alternate local port without editing source files.
- Make the Links lane a compact, readable directory of ordinary hyperlinks.
- Use three columns on expanded screens, two on medium screens, and one on compact screens.
- Keep a visible hostname beneath each linked title so similarly named destinations remain distinguishable.
- Preserve the existing resource-links API and local JSON storage format.
- Make Links list, add, and remove operations work with or without `LOCAL_API_KEY`.
- Provide actionable loading, empty, authentication, server, save, and removal states.

## Non-Goals

- Do not change or migrate the shared `%LOCALAPPDATA%\smcr-staff-ai` data root.
- Do not modify the personal checkout before the project change is published.
- Do not add link analytics, recent-link tracking, pinning, or favorites storage.
- Do not add external link checking or claim that a destination is current or authoritative.
- Do not redesign the other dashboard lanes.

## Confirmed Root Cause and Reliability Design

`apiFetch` will distinguish transport reachability from application responses:

- A rejected `fetch` call is a transport failure. It increments the consecutive transport-failure counter and produces an error with `isNetworkError = true`.
- Any received HTTP response, including `401`, `404`, `422`, or `500`, proves that the local server was reached. It resets the transport-failure counter before status-specific handling.
- JSON parsing failures are response/content errors, not connection failures.
- The global “Connection lost” banner appears only after three consecutive rejected fetches.
- The “Cannot reach local server” banner remains reserved for a primary workspace load that fails at the transport layer.
- HTTP application errors remain attached to the relevant panel or action and never change global connection state.

This preserves the existing retry behavior while removing timing-dependent false alarms from optional startup resources and background refreshes.

## Duplicate-Instance Startup Design

Both launch scripts will support `SMCR_PORT`, defaulting to `8000`.

Before starting Uvicorn, a small Python preflight will test whether `127.0.0.1:<port>` is already accepting connections. If occupied, startup will stop with a concise message that includes:

- the occupied port;
- the current checkout path;
- a reminder that another SMCR Staff AI checkout may already be running; and
- instructions to stop the other instance or set `SMCR_PORT` to another local port.

The check is advisory and local. It will not stop another process, inspect unrelated process details, change the shared data root, or expose the app beyond loopback.

## Links Information Architecture

The dominant job is opening a known staff resource quickly. Browsing and managing personal links are secondary.

The lane will render in this order:

1. A compact header with the title, result count, Search field, category selector, and `Add link` action.
2. A `My links` directory section when personal links exist.
3. An `All resources` directory grouped by category.
4. The add-link form in a collapsible drawer below the header controls.

The existing global Command Post remains unchanged. The redundant Links intro panel will be folded into the directory header so useful content reaches the first viewport sooner.

## Link Presentation

Links will not use pill, chip, badge, or button styling.

Each directory entry contains:

- an underlined linked title;
- the normalized hostname in smaller muted text;
- an optional visible description when one exists; and
- a small `Remove` action only for user-created links.

External links continue to open in a new tab with `rel="noopener noreferrer"`. The accessible name will make the new-tab behavior clear without requiring hover.

Category blocks use semantic headings and lists. Category filtering uses one native select control rather than ten filter buttons. Search matches title, hostname, description, category label, and tags without changing the stored data.

## Responsive Layout

- Expanded (`>= 1100px`): three category columns.
- Medium (`700px` to `1099px`): two category columns.
- Compact (`< 700px`): one column, stacked controls, no horizontal page overflow.

The grid uses `minmax(0, 1fr)` so long titles and hostnames wrap inside their column. Search and category selection remain visible above results at every width.

## Links State and Error Handling

- **Loading:** announced status inside the Links directory with reserved space.
- **No personal workspace:** explain that a personal workspace is required and offer the existing Workspace lane action.
- **No results:** show the active search/filter and a Clear filters action.
- **Load failure:** show the actual safe error message and Retry.
- **Authentication failure:** explain that the workspace passkey must be corrected; do not label it a lost server.
- **Save success:** announce the saved link and refresh results without resetting search/category state.
- **Save failure:** retain entered form values and show an inline error.
- **Remove failure:** retain the entry and show an inline error; do not silently swallow it.

All resource-links GET, POST, and DELETE calls will pass `{ auth: true }` so `apiFetch` supplies `X-Local-API-Key` when configured.

The add form will use server-provided category labels and default user-created links to `Unit-specific`, matching the API schema.

## Accessibility

- Use `section`, headings, `ul`, and `li` for the directory structure.
- Give Search and category controls explicit labels.
- Use an `aria-live="polite"` region for non-critical loading and save feedback.
- Use an alert region for actionable load/auth/remove failures.
- Preserve visible focus treatment on links and controls.
- Keep action target sizes usable without making hyperlinks look like buttons.
- Ensure filtered result counts and no-results state are available as text.

## Files and Responsibilities

- `app/static/dashboard/dashboard.js`: transport-state classification, Links state/rendering, authenticated requests, search/filter behavior, and actionable feedback.
- `app/static/dashboard/index.html`: semantic Links directory shell and compact controls.
- `app/static/dashboard/dashboard.css`: multi-column directory, text-link styling, responsive reflow, and Links states.
- `app/startup_preflight.py`: loopback port-availability check and user-facing diagnostic.
- `start.bat` and `start.sh`: `SMCR_PORT` support and preflight invocation.
- `tests/e2e/test_dashboard_flows.py`: browser regressions for banner classification, Links interaction, keyboard behavior, and compact layout.
- `tests/test_auth.py` or a focused resource-links route test: authenticated Links CRUD coverage.
- `tests/test_startup_preflight.py`: open/occupied port behavior without stopping external processes.

## Acceptance Criteria

- Three expected `404` responses do not show either global connection banner.
- Three rejected fetches show the connection-lost banner deterministically.
- A later received HTTP response clears transport-loss state, regardless of response status.
- `401`, `404`, `422`, and `500` responses remain request-level errors.
- Links list/add/remove work with `LOCAL_API_KEY` configured and unconfigured.
- Search and category filtering can be combined and cleared.
- The active result count is visible and announced.
- Linked titles look like ordinary hyperlinks, with hostname and optional description visible without hover.
- Directory layout is three columns at 1280px, two at 768px, and one at 375px.
- No horizontal page overflow occurs at 375px, 768px, or 1280px.
- Add-link category defaults to `Unit-specific` and uses server labels.
- Load, empty, no-results, auth error, save success/failure, and remove failure states are actionable.
- An occupied configured port produces a clear startup message and does not stop the owning process.
- The full tracked test, type-check, lint, and browser suites pass before publication.

## Risks and Mitigations

- **Large single-file frontend:** Keep the change limited to the existing Links seam and transport helpers; do not refactor unrelated dashboard code.
- **Shared data between checkouts:** Preserve the storage schema and avoid concurrent write tests against the real local data root.
- **Port preflight race:** Treat preflight as explanatory UX, while Uvicorn remains the final authority on binding.
- **External destination freshness:** Display links as stored references only and retain the project’s draft/current-source warning.
