# Handoff — 2026-06-10 — claude-fable

## What I did

- **Security pass** (commit 72c2279):
  - Closed residual auth gaps on `/personnel/*`, `/source-updates/*`, `/documents/*`
    — same class as #9, missed in that pass. All now gated by `LocalApiKeyDependency`.
  - #17: upload `document_type` validated against the enum; unknowns fall back to
    "other" instead of reaching storage raw. Regression test added.
  - Verified safe (no change): privacy-sweeper subprocess (list-form args, no shell,
    server-anchored cwd), `context_id` strict-regex validation (no path traversal).
- **#19 + #20** (commit 53187df): privacy sweeper no longer accepts caller-supplied
  `repo_root` (was arbitrary filesystem enumeration); startup WARNING when
  `LOCAL_API_KEY` is unset.
- **MOS agent consolidation** (commit 31b2df7): compiled 8 near-identical MOS agent
  files into one data module (`mos_advisor.py` — spec dataclass + renderer + 8 data
  rows). All IDs/content/references preserved. Agent files 38 → 30.
- **Roadmap refresh** (commit 2636f2c, #14): honest Shipped / Stub / Priorities.
- Built this **cross-account handoff system** (`docs/handoffs/`).
- Closed issues: #10, #14, #16, #17, #19, #20.

## State at handoff

- Branch / commit: `main` at 72c2279 (this handoff commit will be on top)
- Tests: 518 passed, 0 failed
- Pushed: yes (in sync with origin before this handoff commit)

## What I deliberately did NOT do (and why)

- **Staff echelon registry trim** (106 → ~35) — needs a maintainer decision on which
  echelons are "used" (mef/hqmc keep or generate-on-demand?) and rewrites pinned test
  expectations. Product decision, not mechanical. Fable assessment flagged it
  lower-urgency.
- **Planning cluster collapse** (MCPP/R2P2/OPT/assessment → 1) — same: a product
  decision about whether those are distinct advisors or modes of one. Tests pin them.
- **~103 pre-existing ruff errors** — predate this whole session (mostly import
  sorting). Left alone to avoid colliding with Codex; safe to batch-fix later.

## Open threads I opened or touched

See `README.md` → Current Open Threads for the full living list. Highlights:
- MOS coverage expansion (#7) is now cheap — add a `MosAdvisorSpec` data row.
- Empty content panels (#2/#5/#6) may already populate now that the CWD path bug is
  fixed — **verify before building new content.**
- RAG and SQLite DB both await a cut-or-build decision.

## For the next account

- **Single most important thing:** the dashboard's "empty/broken" reputation was
  substantially the CWD launch-directory path-bug class (#1/#21/static mount), now
  fixed. Before anyone builds new content for the history/reading/doctrine panels,
  **launch the app from outside the repo root and confirm what actually renders.**
  The content may already be there.
- Codex and I share the working tree. `git push` from either pushes both our commits —
  history stays linear, but always `git fetch` and check `origin/main..HEAD` before
  assuming you're ahead.
- The repo is being prepped for the FHG AI initiative upload. Optimize for
  reviewer signal-to-noise: honesty in labeling > surface area. ARCHITECTURE.md is
  the intended reviewer entry point.
