# Dashboard Bundle Remediation Plan

**Status (2026-07-12, updated again):** Steps 0 and 1 done and committed. Step 2 is
substantially further along: **Actions, custom watch Feeds, resource Links, and
profile identity fields (via session Handoff) are all wired to the real backend and
verified end-to-end in a live browser** — add/edit/toggle/delete round-trip through
the actual API and survive a reload. The due-date field mismatch flagged in the first
pass is also fixed (free-text "due" now round-trips correctly instead of only showing
up in Notes after reload). Still demo-only: the personal notebook/logbook, the rich
scored FitRep writer, benchCards (file/template/doctrine reference cards), travel
status, and "save to project" — each needs either a backend design decision or new
endpoint before it can be wired the same way (see "Remaining state domains" below,
now updated with concrete per-domain findings from checking every relevant schema).

**Context:** The compiled Claude-design-tool bundle (`app/static/dashboard/index.html`,
2.3MB, merged via commits `3f2bf82`/`de9a99e`/`c54b742`) replaced the working,
backend-wired dashboard with a static prototype. A Fable review (2026-07-12) flagged
this as not release-ready. I independently verified every claim below against the
current code — all confirmed true. This doc scopes the fix.

**Decision (user, 2026-07-12):** Keep the bundle's visual design. Wire it to the
real backend rather than reverting. Backend routes/services are untouched and fully
functional — this is a frontend rewiring job, not a backend rebuild, **except** for
the one net-new feature (drafted-files/"save to project") which has no backend at all.

---

## Verified findings (all confirmed by direct inspection, 2026-07-12)

| # | Claim | Verified | Evidence |
|---|---|---|---|
| 1 | No backend calls in bundle | ✅ | 2 `fetch()` hits total in 2.3MB file — both are the bundler's own script-loader (line offsets 6579, 9084), not app data calls. Zero `apiFetch`, zero `localStorage`, zero `sessionStorage`. |
| 2 | Old dashboard.js had 60 real API call sites across 13 endpoint prefixes | ✅ | `git show ecd5028:app/static/dashboard/dashboard.js \| grep apiFetch` → exactly 60 matches, endpoints: `/bench-sections/`, `/custom-mos-recipes/`, `/custom-watch-feeds/`, `/dashboard/data/`, `/handoffs/`, `/modules/`, `/personal-documents/`, `/product-templates/`, `/reading-list/state/`, `/resource-links/`, `/section-memory/`, `/staff/battle-rhythm/`, `/user-profile/`. |
| 3 | Backend routes/services for those endpoints still exist and work | ✅ | `app/api/routes/dashboard.py` still defines `get_dashboard_data` (`/dashboard/data/{user_key}`), `get_demo_dashboard_data`, and 25+ dependency-injected service getters — none were touched by the bundle merge. Only the frontend stopped calling them. |
| 4 | CI runs the broken e2e suite (would fail/hang on every future PR) | ✅ | `pytest tests/ --collect-only` → 583 tests collected, includes all of `tests/e2e/`. `pytest.ini` has no `addopts` marker exclusion. CI (`.github/workflows/ci.yml:39`) runs bare `pytest tests/ -q` — no `--ignore=tests/e2e`, no `-m "not e2e"`. |
| 5 | e2e tests target selectors that no longer exist in the bundle | ✅ | 18 e2e test functions across `test_dashboard_flows.py` (11) and `test_links_directory.py` (7), referencing IDs like `#tab-overview`, `#load-demo`, `#workspace-note`, `#readiness-posture`. Grepped all of them against the bundle: **zero matches for any.** |
| 6 | Shell test weakened to string-presence checks only | ✅ | `tests/test_dashboard.py:53-66` now asserts `"__bundler/manifest" in response.text` and a few label strings — no assertion that any element is wired to a handler or backend call. |
| 7 | Reveal endpoint bypasses real auth | ✅ | `app/api/routes/dashboard.py:91-96` — gate is `x_smcr_dashboard != "1"`, a hardcoded literal header value, not `LocalApiKeyDependency` (the pattern used by every other sensitive route, e.g. `app/api/routes/resource_links.py:20`). Any page that can send a custom header to `localhost:8000` can trigger an OS file-explorer launch. |
| 8 | Missing-file reveal requests silently succeed at the wrong path | ✅ | `app/api/routes/dashboard.py:116-120` — walks up to nearest existing ancestor (falls back all the way to repo root) and still returns `{"status": "opened", ...}`. No distinction between "opened what you asked for" and "opened somewhere else because your path didn't exist." |
| 9 | Hardcoded demo content baked into bundle (not computed) | ✅ | Literal strings `"18 days"`, `"Good evening"` found in the raw bundle. Also `"combination"` / `"combo"` text present — the mockup's travel/gear sections include an example locker-combination field, which is a bad pattern to ship even as a demo default. |
| 10 | No responsive breakpoints, no dialog ARIA | ✅ | `grep -c '@media'` → 0. `grep -c 'role="dialog"\|aria-modal'` → 0. |
| 11 | Missing page metadata | ✅ | `<title>Bundled Page</title>` (not the app name). `<html>` has no `lang` attribute (found twice, oddly — worth checking why two `<html>` tags appear in the source at all). |
| 12 | "Save to project" / drafted-files feature has no backend | ✅ | `grep -rln 'workflow_doc\|draft_doc\|_drafts\|DraftDocument' app/` → zero matches. This isn't a "reconnect" — there is no backend counterpart to build against. Net-new work. |

---

## Fix plan, in dependency order

### Step 0 — Stop the bleeding (small, do first, unblocks all other PRs)
- Add `-m "not e2e"` to CI's `addopts` in `pytest.ini`, OR change the CI step to
  `pytest tests/ -q --ignore=tests/e2e` (matches what we've been doing locally).
  Either works; prefer the `pytest.ini` addopts change so local `pytest tests/`
  matches CI behavior everywhere, not just in the one workflow file.
- This does **not** fix the e2e tests — it just stops them from silently breaking
  CI while the real fix (Step 4) is pending.

### Step 1 — Secure the reveal endpoint
- Replace the `x_smcr_dashboard` header check with `LocalApiKeyDependency` (same
  pattern as `resource_links.py`). If the dashboard truly needs to reach this
  endpoint without a configured key (key is optional in this app — unset means
  no gate), keep the local-only intent but stop relying on a hardcoded literal
  the client fully controls.
- Fix the silent-success-at-wrong-path issue: either 404 when the requested path
  doesn't exist (drop the "nearest ancestor" fallback), or return a response that
  distinguishes `resolved == requested` from `resolved != requested` so the
  frontend can show "opened a parent folder instead" rather than implying success.

### Step 2 — Wire the bundle to real data (the core of the P0)

**Architecture discovery (supersedes the "two approaches, unknown which" framing
below from the first pass at this doc):** The bundle is not opaque. It's a
Claude-design-tool export whose `<script type="__bundler/manifest">` holds a
26-asset map (fonts, one PNG, React 18 + ReactDOM production builds, and a
64KB "dc-runtime" — the tool's own template interpreter). The entire app view
+ logic lives as ONE JSON-string-encoded blob in a sibling
`<script type="__bundler/template">` tag. Decoded, that string is a normal,
readable HTML document containing a `<script type="text/x-dc" data-dc-script="">`
block with a plain `class Component extends DCLogic { state = {...}; ... }` —
a single-component, React-class-shaped app with a flat state object and
ordinary methods (`addAction()`, `toggleActionDone(id)`, `componentDidMount()`,
etc). `DCLogic.setState()` re-renders through the wrapping React component;
`componentDidMount()` is a real lifecycle hook. **Approach (a) below did not
end up mattering** — editing the decoded source directly and re-encoding it is
entirely tractable and is what actually got used (approach (b), but concrete
rather than reverse-engineered, since the source turned out to be readable).

**Tooling:** `scripts/patch_dashboard_bundle.py` does the decode → patch →
re-encode cycle safely. Patches are exact-string find/replace pairs against
the *decoded* component source; the script aborts loudly (no write) if a
patch's target text isn't found exactly once, so a future re-export from the
design tool can't silently corrupt or double-apply a patch. **Gotcha already
hit and fixed:** the original export escapes every `</` as `/` inside the
JSON string so embedded closing tags (`</script>`, `</head>`, ...) can't be
mistaken by the outer HTML parser for the end of the `__bundler/template`
element itself. `json.dumps()` does not do this by default — the script
replicates it by post-processing, and self-verifies by re-decoding what it
just wrote before declaring success. Run `uv run python
scripts/patch_dashboard_bundle.py --check` for a dry run, or without `--check`
to apply and write.

**Done so far — Actions tracker, full CRUD, verified live:**
- `_resolveUserKey()`: reads/generates `localStorage["smcr_user_key"]`,
  matching the pre-bundle `dashboard.js`'s exact key name and
  `crypto.randomUUID()` generation, so a browser that already used this app
  reaches the same stored personal data.
- `_apiHeaders()`: attaches `X-Local-API-Key` from `window.__SMCR_API_KEY__`
  (injected by the `/dashboard` route from `get_settings().local_api_key`,
  same mechanism as the reveal-shim fix in step 1) when one is configured.
- `componentDidMount()` now also calls `_loadRealWorkspace()`, which fetches
  `/dashboard/data/{userKey}` and replaces the hardcoded demo `actions` array
  with `tracked_actions` from the response.
- `addAction`, `toggleActionDone`, `deleteAction` now call
  `POST /actions/track`, `PATCH /actions/{id}`, `DELETE /actions/{id}`
  respectively, with optimistic local updates and rollback-on-failure.
- Verified end-to-end in a live browser (not just unit tests): added a real
  action through the actual form UI → confirmed `POST /actions/track` fired →
  confirmed the record exists server-side via a direct fetch with real
  `action_id`/timestamps/history → **reloaded the page and the action
  survived** (the core P0 this whole remediation exists to fix) → toggled
  done via a real checkbox click → confirmed `PATCH` fired and server-side
  `status` changed to `"closed"` → deleted via the UI → confirmed `DELETE`
  fired and the record is gone server-side. All other lanes (Overview, Bench
  / Files, Workflows, Workspace, Links) still render with no new console
  errors after the patch.
- Pinned with `tests/test_dashboard.py::test_dashboard_bundle_is_wired_to_real_actions_api`,
  which decodes the served bundle and asserts the real-fetch code is present
  — so a careless future bundle re-export that drops this wiring fails CI
  instead of failing silently at runtime.

**Due-date field mismatch: fixed.** `_mapRealAction` now parses the `"Due:
<text>"` prefix back out of `notes` on load (`dueMatch` regex), so a `due`
value typed on create (e.g. "before drill", "overdue", "15 AUG") shows up
correctly in the Due column after a reload instead of leaking into Notes.
Verified live: created an action with `due: "before drill"`, confirmed the
server stored `notes: "Due: before drill"`, reloaded the page, confirmed the
UI showed `Due · before drill` (not "unscheduled", not stuck in Notes).

**Feeds — done (load + create + delete), verified live.** Custom watch feeds
are a global backend store (`/custom-watch-feeds`, no per-user scoping — the
route list confirmed this: `GET/POST ""`, `PATCH/DELETE "/{feed_id}"`, no
`user_key` anywhere). The 4 built-in demo feeds (MARADMIN/NAVADMIN/Gazette/unit
bulletin) have no backend equivalent and stay local, marked apart from real
ones via an `isReal` flag so `removeFeed` only calls DELETE for feeds that
actually exist server-side. `CreateCustomWatchFeedRequest.url` is a required
`HttpUrl`, but the bundle's UI supports a "manual — no source URL" feed type;
those stay local-only (can't be created server-side as-is). Trust labels
("Official"/"Professional"/"Unit"/"Custom") map to the backend's
`CustomWatchFeedTrustLevel` enum via a small lookup table. **Not wired:**
inline editing of an existing feed's fields (`toggleFeedEdit`/
`updateFeedField`) — the backend supports `PATCH`, but the current UI has no
explicit "save" commit point for those live-per-keystroke fields, and wiring
it well needs the same debounce treatment as profile fields below; scoped out
to keep this pass bounded. Verified live: added a feed through the real form,
confirmed `POST /custom-watch-feeds` fired and persisted with a real
`feed_id`/timestamps, removed it through the UI, confirmed `DELETE` fired and
it's gone server-side.

**Links ("A Few Good Links") — done (load + create), verified live.** Unlike
feeds, `/resource-links/{user_key}` already has real seed data
(`data/seed/resource_links.json`) serving the same "always show curated
links" role the bundle's hardcoded `linkGroups` served, so this **fully
replaces** `linkGroups` from the real fetch on load rather than merging —
after wiring, the Links tab shows the actual seed catalog (IPPS-A, milConnect,
DTS, etc.) instead of the bundle's own smaller hardcoded set. The category
field is a fixed 10-value enum (`ResourceLinkCategory`) but the bundle's "Add
link" form is free text; `_categoryKeyForLabel` matches typed text against the
fetched category labels case-insensitively and falls back to `"unit"`.
**Not wired:** no delete-link UI exists in the bundle at all (not a regression
— it never had one), though the backend supports `DELETE`; adding that button
means touching the HTML template, not just component logic, deferred. Verified
live: added a link through the real form with category "Admin & pay", confirmed
`POST /resource-links/{user_key}` fired and persisted with `category:
"admin_pay"` (correct label→enum mapping) and a real link `id`.

**Profile identity fields — done (load + debounced save), verified live.**
`profileRank`/`profileLastName`/`profileBillet`/`profileUnit` map to
`UserSessionHandoff.rank`/`display_name`/`billet`/`unit_id` via
`/handoffs/{user_key}` — **not** `/user-profile/{user_key}`, which is a
separate, smaller concept (format preference / style notes only). No explicit
"Save" button exists in this drawer (fields save live per keystroke in the
demo), so real saves debounce 800ms after the last change via
`_scheduleHandoffSave` → `PUT /handoffs/{user_key}` with the previously-loaded
handoff object as a base (so fields this UI doesn't expose, like
`admin_watch_items` or `fitreps` reminders, aren't clobbered). A 404 on load
is treated as normal (brand-new profile, fields stay blank) rather than an
error. Verified live: typed a rank and last name, waited past the debounce,
confirmed `GET /handoffs/{user_key}` returned `display_name: "Capt TestE2E"`
and `rank: "Capt"` server-side.

**Also discovered, not yet fixed:** the hardcoded date/greeting strings from
finding #9 (`"18 days"`, `"Good evening"`) are still present — untouched by
this pass. Same tool, same pattern; natural next small patch.

**Remaining state domains, still demo-only:**
- **Personal notebook/logbook** (`notes` — locker combos, running notes,
  free-form title+body) — checked `/section-memory/{user_key}` as the closest
  candidate; its schema (`recurring_questions`/`recurring_failure_modes`/
  `preferred_checks`/`notes: list[str]` per named section) is structured for a
  different purpose, not free-form title+body notes. **No clean backend match
  — needs a new lightweight endpoint**, or a deliberate decision to repurpose
  something.
- **FitRep writer** (`fitreps` — 5 scored traits, statement, RO comments,
  relative-value tree per Marine) — checked `UserSessionHandoff.fitreps`;
  it's `FitrepReminder` (`occasion`/`due_date`/`role`/`notes`), a due-date
  *reminder*, not a scoring tool. **No backend match — this is genuinely new
  backend work**, not a wiring job, if the bundle's rich writer is to be kept
  as-is.
- **"Save to project" / drafted files** — confirmed zero backend, see finding
  #12 and Step 3 below.
- **benchCards** (file/template/doctrine reference cards) — partial matches
  exist (`/product-templates`, `/personal-documents`) but need per-card
  investigation; some entries (doctrine reference URLs) are fine to leave
  hardcoded since they're just links, not user data.
- Not investigated this pass: quote-of-the-day rotation, today-in-history,
  travel status, staff-lane doctrine/resources/prompts (per staff-lane modal),
  quickLinks (the small Overview-pinned subset, distinct from the full Links
  directory above — likely fine as a client-side "pin" list referencing the
  now-real link data rather than needing its own backend).

The reference pattern to extend any of these: (1) confirm the backend
endpoint and exact schema shape (don't assume — check, as the FitRep/notes
findings above show assumptions here are often wrong), (2) add a `_loadX()`
call from `componentDidMount`, (3) rewrite each mutation method to call the
real endpoint with optimistic update + rollback, (4) add patch-tool entries
(remember: idempotent by design now, checks `new` text first — see the
`apply_patches` docstring), (5) verify live in a browser end-to-end including
a reload, (6) pin with a test like the ones added for actions/feeds/links/handoff.

### Step 3 — Build the missing "save to project" backend (net-new, finding #12)
- Design a minimal endpoint (e.g. `POST /dashboard/drafts` and
  `POST /dashboard/drafts/{id}/save-to-project`) that actually writes `.md`
  files under `projects/{project}/products/` per the existing `AGENTS.md`
  project-save conventions (dual-format `.md`+`.docx`, see
  `smcr-staff-ai-personal` conventions if this repo doesn't already have them —
  check `app/services/staff_products/` or similar first, this may already
  partially exist for other flows).
- File uploads: same gap — currently only filenames are retained. Needs a real
  multipart upload endpoint if this feature is worth keeping, or drop it from
  the UI if out of scope for this pass.

### Step 4 — Rewrite the e2e test contract (finding #5)
- Once Step 2 is done and the bundle's real element structure is known
  (whatever IDs/selectors the design-tool export uses, or whatever the adapter
  layer exposes), rewrite `tests/e2e/test_dashboard_flows.py` and
  `test_links_directory.py` against the new selectors.
- Also restore `tests/test_dashboard.py`'s shell test to assert real behavior
  (e.g. that the workspace bootstrap call fires, not just that a string like
  `"Bench / Files"` appears in a 2.3MB blob).

### Step 5 — Accessibility & responsive pass (P1, do after functionality is real)
- No `@media` queries at all — needs breakpoints for mobile/tablet, matching
  the reflow requirements the review cited (WCAG 1.4.10).
- Dialogs/overlays need `role="dialog"`, `aria-modal="true"`, focus trap, and
  Escape-to-close (W3C APG modal pattern) — currently none.
- Tab selection state needs to be programmatic (`aria-selected`), not just
  visual styling.
- Checkboxes need accessible names.
- Fix `<title>Bundled Page</title>` → real app title, and add `lang="en"` to
  `<html>`.

### Step 6 — Bundle size / perf (P2, lowest priority)
- 2.3MB with no cache headers on `/dashboard`. Add `Cache-Control` headers for
  the static bundle response (it changes rarely).
- The 3000×3000px / 1.10MiB PNG rendered at 22×22px should be replaced with a
  properly-sized asset or an inline SVG (the original mockup already had an SVG
  crest icon available — check if it's still in the design-tool source).

---

## Open questions for the next session
1. Does the Claude design-tool support re-binding `{{ }}` template variables to
   a live fetch layer, or is post-export adaptation (approach 2b) the only path?
   This determines whether Step 2 is a re-export or a reverse-engineering job.
2. Is there already a "save staff product to project" backend anywhere in this
   repo (check `app/services/staff_products/`, `app/api/routes/staff_products.py`)
   that the bundle's "save to project" button could target instead of building
   new? Grep turned up nothing under the `_drafts`/`workflow_doc` naming the
   bundle uses, but a differently-named existing feature might already cover
   this.
3. Confirm whether file uploads (receipts, orders) are in scope for this pass
   or should be deferred — they're a smaller P1/P2 concern relative to the core
   data-persistence P0.
