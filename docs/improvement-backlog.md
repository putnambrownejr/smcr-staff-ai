# Improvement Backlog

Findings from structured skill-based review passes. Each item has a severity, source, and status so we can pick up work across sessions without re-deriving context.

**Severity codes:** H = High (significant friction), M = Medium (noticeable friction), L = Low (polish)
**Status codes:** open | in-progress | done | deferred

---

## Round 1 — Dashboard UX Review + Fortify (2026-06-12)

Score: **30/50** (Revise range). Solid structure, repeating gap patterns in feedback loop, keyboard contract, and edge-case messaging.

### High

| ID | Finding | Fix summary | Status |
|----|---------|-------------|--------|
| H1 | No per-widget loading or success feedback — saves/refreshes are silent until complete; workspace-note at top is too far from action point | Disable triggering button during fetch, show spinner/label swap on it, show inline success near the panel | done |
| H2 | Arrow key navigation missing from tab bar — ARIA tab pattern requires ←/→ to move between tabs; only Tab key works now | Add `keydown` handler on tablist for `ArrowLeft`/`ArrowRight` that moves focus + `aria-selected` and calls `openLane()` | done |
| H3 | No general `:focus-visible` style — only skip link gets explicit focus styling; buttons and inputs rely on browser defaults which CSS likely suppresses | Add `*:focus-visible { outline: 2px solid <accent>; outline-offset: 2px; }` to `dashboard.css`; remove any bare `outline: none` | done |
| H4 | Silent error swallowing on individual refreshes — multiple `catch (_error) {}` blocks discard failures entirely | Replace silent catches with at minimum `setWorkspaceNote(error.message, true)` or inline error indicator near the triggering panel | done |

### Medium

| ID | Finding | Fix summary | Status |
|----|---------|-------------|--------|
| M1 | No "last refreshed" timestamp on any feed panel — stale data looks identical to fresh | Display "Last updated: X min ago" below each refreshable panel; MARADMIN feed already tracks fetch state, surface it | done |
| M2 | Drawer label static — `<span class="drawer-label">Open</span>` doesn't change when expanded | Toggle label on `toggle` event: `el.open ? 'Close' : 'Open'` | done |
| M3 | Empty states don't distinguish "not loaded" vs "nothing exists" — pre-load and genuinely-empty states look identical | Two distinct messages per panel: greyed "Load workspace to see this" (pre-load) vs "Nothing here yet — add your first X" (post-load empty) | done |
| M4 | No mobile breakpoint below 980px — phones have no intentional layout adaptation | Add `@media (max-width: 600px)` block: single-column stack, tab bar wraps or becomes a select, timezone panel collapses | done |
| M5 | First-run onboarding is three verbose cards before user can act | Single prominent "Open demo workspace" CTA + one-sentence label; move explanation to `<details>` | done |
| M6 | Concurrent refresh clicks not guarded — no debounce, no disable-during-fetch | Disable all refresh buttons in the group while any one is in-flight; re-enable together on completion | done |

### Low

| ID | Finding | Fix summary | Status |
|----|---------|-------------|--------|
| L1 | Stale handoff banner uses bare emoji `⚠` with no text alternative | `<span aria-hidden="true">⚠</span><span class="sr-only">Warning:</span>` | done |
| L2 | Command Post guardrails/mission focus render as empty bullet lists pre-load | Hide the lists until workspace loads, or show subtle "—" placeholder | done |
| L3 | History fact is buried in Watch lane behind a drawer | Add small persistent card on Overview for history fact | done |
| L4 | Browser back button navigates away instead of restoring previous lane | Push `#overview`, `#watch` etc. to `history.pushState` on lane change; handle `popstate` | done |
| L5 | Source watch has 3 refresh buttons in one row with no grouping indicating which refreshes which | Visual grouping label or consolidate into a single "Refresh all" with per-panel state | done |

### Fortify — Edge Cases

| ID | Scenario | Current behavior | Fix | Status |
|----|---------|-----------------|-----|--------|
| F1 | API server not running | Error surfaces in `#workspace-note` — may be missed | Prominent "Cannot reach local server — is the app running?" state with restart instructions | done |
| F2 | First-time user, all stores empty | Every panel shows empty-state simultaneously — reads as broken | Show single "You're all set up — nothing stored yet" orientation message instead of 15 simultaneous empty states | done |
| F3 | Demo endpoint failure | No fallback | "Demo unavailable — try reloading" with retry button | done |
| F4 | Very long content (200+ char MARADMIN title) | Unknown — no max-width guard observed | `overflow-wrap: break-word` + `max-height` with overflow scroll on feed items | done |
| F5 | Long session / server restart mid-session | Fetches fail silently after restart | Detect N consecutive fetch failures → show "Connection lost — reload to reconnect" | done |

---

## Round 2 — Impeccable Polish Pass (2026-06-12)

### Polish

| ID | Finding | Fix summary | Status |
|----|---------|-------------|--------|
| P1 | `--accent` undefined — focus ring falls back to #4a90d9 (generic blue) that clashes with palette | Add `--accent: #5a9fd4` to `:root` | done |
| P2 | Zero CSS transitions — all hover/state changes snap instantly | Add `transition: filter 120ms ease, background-color 120ms ease…` to buttons and form controls; add `prefers-reduced-motion` guard | done |
| P3 | No `button:disabled` style — browser defaults show through when buttons are disabled during fetch | `button:disabled, button[disabled] { opacity: 0.45; cursor: not-allowed; pointer-events: none; }` | done |
| P4 | Form controls have no dedicated focus style beyond global outline | `input:focus-visible, select:focus-visible, textarea:focus-visible { border-color: var(--accent); background: var(--surface-2); }` | done |
| P5 | Topbar gradient uses hardcoded hex (`#08090b`, `#11161b`) instead of CSS variables | Replace with `linear-gradient(180deg, var(--bg) 0%, var(--surface) 100%)` | done |
| P6 | Pure `#fff` on button text and skip link against scarlet background | Replace with `#f5ebe9` (warm-tinted near-white) | done |
| P7 | No `button:active` press feedback — click has no visual response | `button:active, .lane-button:active { filter: brightness(0.88); }` | done |

---

## Round 3 — Issue #4: Configurable Section Bench Notebook (2026-06-12)

Feature: user can add/remove sections from the bench notebook dropdown.
Commit: `8cf5a1c` — closes #4. 505 tests passing.

- New schema: `BenchSectionsConfig`, store: `BenchSectionsStore`, route: `/bench-sections/{user_key}`
- Frontend: dynamic dropdown populated from API, inline Manage editor (no modal)
- 5 new tests covering store and route behaviors

---

## Round 4 — E2E Test Scaffolding (2026-06-12)

Commit: `69d9717`. 5 Playwright flow tests written and skipped pending install.

**To activate:** `uv add playwright --dev && playwright install chromium && pytest -m e2e tests/e2e/`

Covered flows: demo workspace load, lane tab navigation, bench section manage editor, refresh button feedback, server-down banner (manual).

---

## Round 5 — Architecture Blueprint (2026-06-12)

Four cut-or-wire decisions resolved:

| Decision | Verdict |
|---|---|
| SQLite for feeds/history | **Cut** — flat JSON correct for single-user local tool; add `MAX_FEED_ENTRIES` trim instead |
| MOS advisor agent registry | **Cut** — frozen dataclass rows are correct; extend via YAML override if needed |
| dashboard.js module split | **Wire when ready** — split is safe at ~4000 lines or second contributor |
| Multi-user/shared-workspace | **No action** — `user_key` seam is clean; add `group_key` when needed |

### Blueprint Open Actions

| ID | Action | Status |
|----|--------|--------|
| B1 | Add `MAX_FEED_ENTRIES = 200` trim to MARADMIN feed store on write | in-progress |
| B2 | Remove `database_url` / `vector_store_backend` dead config or mark reserved | in-progress |
| B3 | Document `user_key` → `group_key` extension point in `docs/architecture.md` | done |
| B4 | Add module-split readiness note to `dashboard.js` header | done |
