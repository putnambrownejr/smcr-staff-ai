# Cross-Account Handoffs

This is the relay point for work passed between accounts, agents, and machines
through GitHub. The maintainer's main account, reviewer accounts, Claude (Code /
Fable), and Codex all push to the same repo — this directory is how they hand off
state without stepping on each other.

## Why this exists separately

Session state does not belong in `docs/core_documents/` — that directory is for
authoritative, durable docs (project purpose, roadmap, architecture). Mixing
session scratch with authoritative docs signals "these people don't curate."
Handoffs live here instead. Authoritative docs link forward; handoffs are
disposable history.

## Privacy boundary

These files are committed to the **public** repo. They are for *project and code*
state only — no personal admin, names, drill specifics, or PII. Anything personal
belongs in the separate `smcr-staff-ai-personal` repo, never here. If a handoff
needs to reference personal context, summarize it generically ("a travel-claim
workflow") rather than including the detail.

## The convention (simple, conflict-free)

1. **One file per handoff, dated and attributed.** Name it:
   `HANDOFF_YYYY-MM-DD_<who>.md` — e.g. `HANDOFF_2026-06-10_claude-fable.md`,
   `HANDOFF_2026-06-11_codex.md`, `HANDOFF_2026-06-12_reviewer.md`.
   Unique filenames mean no merge conflicts across accounts.

2. **Copy `TEMPLATE.md`** and fill it in. Keep it short enough to read in 3 minutes.

3. **Add one line to the index below** (newest first). That is the only shared
   edit, and it is one append-only line — conflicts are trivial to resolve.

4. **Update "Current Open Threads"** if your handoff changes the live picture.
   This is the single place anyone looks to answer "where are we right now."

5. **Push.** The next account pulls, reads the top of the index, and continues.

## Index (newest first)

- [HANDOFF_2026-06-10_codex-feedback-pass.md](HANDOFF_2026-06-10_codex-feedback-pass.md) — Post-hardening feedback pass; CI portability fix, ruff/dependency/auth deployment findings. pytest/mypy green locally.
- [HANDOFF_2026-06-10_claude-fable.md](HANDOFF_2026-06-10_claude-fable.md) — Security pass (auth gaps, #17), MOS agent consolidation, roadmap refresh, this handoff system. 518 tests green.

## Current Open Threads

The living "where are we" list. Update when you open or close a thread.

### Decisions waiting on the maintainer
- **RAG: cut or build.** Currently a hash-embedder + lexical stub. Decide whether
  to remove it (lowest cost) or implement real semantic retrieval (only if doctrine
  RAG is the next priority). See ARCHITECTURE.md.
- **SQLite DB: cut or wire.** Five tables defined, zero runtime use. Documented as
  future doctrine-ingestion schema. Decide to keep-as-documented or remove.

### Decided and done
- **MEF/HQMC echelons ditched** (2026-06-10) — division_group is now the top
  supported echelon. 14 staff-advisor agents removed; enum pruned.
- **Planning cluster collapsed** (2026-06-10) — MCPP + R2P2 + OPT merged into one
  `planning-advisor` agent that reads tempo (deliberate vs compressed) from input
  and carries the OPT facilitation discipline. 3 agents → 1, no content lost.
- Registered agents: 106 → 90.

### Ready to work (mechanical, no decision needed)
- **#7 expand MOS coverage** (0602 Comm Officer, SJA/legal, aviation/wing) — now
  cheap: MOS agents are data rows in `mos_advisor.py`. Add a `MosAdvisorSpec`.
- **#8 retire 7 redundant agents** — separate from the MOS data-compile; check the
  issue's list against the current registry.
- **Empty content panels** (#2 history facts, #5 doctrine library, #6 reading list)
  — verify whether the CWD path-bug fix already populates these before building new
  content; the panels may have been empty only because of the launch-directory bug.
- **~100 pre-existing ruff errors** (mostly import sorting, `E402`, and long lines)
  — a dedicated lint pass. Not from recent work; start with safe import sorting,
  then add `ruff check .` to CI once green.
- **Dependency lock/update strategy** — no lockfile or Dependabot config yet.
  Choose `uv`, `pip-tools`, or another project-standard path before enabling
  automated dependency updates.
- **Watch first CI run** — `.github/workflows/ci.yml` now runs pytest and mypy.
  Confirm GitHub Actions is green on `main` after the Codex feedback-pass push.

### Strategic (from the June Fable assessment, archived)
- **Turn-key delivery for non-technical tiers** — a hosted Claude Project / Custom
  GPT preloaded with the skills + reference notes reaches users who want a chat
  surface, not a local install. Cheap because the skills already exist.
- **Set runtime expectations in README** — one line: "the AI reasoning comes from
  your connected assistant; the local app is structured workflows + private storage."
