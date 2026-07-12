# Dashboard Bundle Remediation Plan

**Status:** Fact-finding complete, not yet started. Written for a future session
with full token budget.

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
This is the large piece. The bundle is a single 2.3MB minified/bundled file —
**do not hand-edit it** (per its own header comment). Two possible approaches,
scope each before picking:
- **(a) Re-export from the design tool with data hooks wired**, if the Claude
  design-tool workflow supports binding its `{{ }}` template variables to a real
  fetch layer instead of in-memory mock state. Check whether the original design
  session (still open per the user) can be pointed at the 13 real endpoints from
  finding #2 instead of its built-in demo data, then re-export.
- **(b) Post-process the bundle**: write a thin adapter script injected at serve
  time (same pattern as the existing `reveal-shim.js`) that intercepts the
  bundle's internal state-update calls and mirrors them to/from the real API.
  Likely more fragile than (a) since it means reverse-engineering the bundle's
  internal state contract without source.
- Whichever approach: the 13 endpoint prefixes from finding #2 are the wiring
  checklist. Confirm each one round-trips (create/read/update/delete as
  applicable) before calling this step done.
- Demo mode should stay client-only fake data (that's legitimate — it's a "safe
  tour" mode), but "Personal mode" must actually persist through the real API.
  Fix the date/greeting hardcoding (finding #9) as part of this — those should
  compute from `Date.now()` and the loaded workspace's drill date, not be static
  strings.

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
