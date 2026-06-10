# Repo Feedback — Fable Pass

Date: 2026-06-04
Reviewer lens: architectural / scope altitude (read-only assessment; no code changed)

## How This Pass Differs

Three assessment passes already ran this session and produced GitHub issues #1–#21
plus a security review. Those passes worked issue-by-issue: startup blocker, auth
gaps, PII handling, stale docs, redundant agents, and the systemic CWD-relative
path bug (#21). This pass deliberately does **not** re-list those. It steps back to
the architecture and asks a different question: *is the project carrying weight it
does not use, and is its real spine where the docs say it is?*

The short answer: the project is healthier and more complete than the 21-issue
backlog implies, but it is carrying two large pieces of aspirational scaffolding
(a database and a RAG layer) as if they were load-bearing, when neither is. The
real product is the advisory-agent layer, the JSON file-store continuity layer,
and the dashboard.

## BLUF

- The SQLite database is **vestigial**. Five tables are defined and created by the
  `init_db` step the README instructs users to run, but **no route or service reads
  or writes them at runtime**. The live app persists everything through JSON
  file-stores. There are two parallel persistence stories and one is dead.
- The RAG layer is **interface-only**, not a foundation. The embedder is a hash
  stub; the vector store ignores its own vectors and does keyword overlap. "Ready
  for expansion" overstates what is really a set of function signatures.
- The CWD-relative path bug (#21) is **broader than filed**: `app/main.py` mounts
  static files with a relative path too, so the dashboard's own HTML/CSS/JS will not
  serve if the server is launched from outside the repo root.
- Net read: fix the two path-bug classes (#1, #21, plus the static mount below),
  then decide deliberately what to do with the DB and RAG. Do not keep paying their
  carrying cost by default.

## Net-New Findings (not in issues #1–#21)

### 1. The database is dead weight — decide to wire it or cut it

`app/db/models.py` defines five `SQLModel` tables: `Document`, `DocumentChunk`,
`MessageRecord`, `CalendarPlan`, `OrgUnit`. `init_db()` creates them, and the README
setup flow tells every new user to run `python -m app.db.init_db`.

A search for any runtime import of `app.db` — excluding the table definitions, the
`init_db` entrypoint, and the test suite — returns nothing. No route, no service,
reads or writes these tables during normal operation. Every piece of live state
(handoffs, actions, travel cases, drill plans, section memory, opportunities,
battle rhythm, feeds) is persisted as JSON files under the local-context storage
home instead.

Consequences:
- The setup instructions create a SQLite file that the app never opens. This is a
  silent "why did I do that" step for any contributor who looks closely.
- `GET /documents` returning a hardcoded placeholder (already filed) is a symptom
  of the same disconnect: the `Document` table exists but nothing populates or
  queries it.
- `models.py` carries `classification_label`, `cui_flag`, `source_hash`, and
  effective-date fields that imply a doctrine-corpus ingestion pipeline that does
  not exist yet.

ROI read: this is a *decision*, not a bug. Either:
- **Cut it** (lowest cost): remove the `init_db` step from the README setup flow,
  and either delete the unused tables or move them behind a clearly-labeled
  `docs/` note as "planned schema for future doctrine ingestion." This removes a
  setup tax and a source of reviewer confusion for near-zero effort.
- **Wire it** (higher cost, only if doctrine RAG is actually the next priority):
  make `MessageRecord` and `Document` the real backing store for the ingestion and
  feed routes that currently use JSON files. This is a meaningful refactor and
  should not be done unless RAG-over-doctrine is genuinely the next phase.

Recommendation: cut from the setup flow now, keep the schema as a documented
future target. Do not let new contributors keep running an init step for a database
the app ignores.

### 2. RAG is a shape, not a foundation — relabel the capability

`app/services/rag/` presents as a RAG stack (chunking, embeddings, pipeline,
retriever, vector_store), and both the README capability table and the roadmap
Phase 2 treat it as a base to build on. In practice:

- `embeddings.py` — `LocalHashEmbeddingProvider` returns the first 16 bytes of a
  SHA-256 digest divided by 255. This is deterministic noise, not a semantic
  embedding. Two sentences about the same topic produce unrelated vectors.
- `vector_store.py` — `LocalVectorStore.search()` ignores the stored vectors
  entirely and ranks by lexical term intersection. It is keyword overlap wearing a
  vector-store interface.

This is fine as a placeholder that establishes the *interface shape* — and the
docstrings honestly say "stub" — but the README and roadmap language ("RAG
foundations — ready for expansion") implies there is a foundation to extend. There
is not. Any real RAG work replaces both files wholesale.

ROI read: near-zero-cost relabel. Change the README capability line from "RAG
foundations" to something like "RAG interface stubs (hash embedder + lexical store;
no semantic retrieval yet)" so a contributor or evaluator does not assume there is
retrieval quality to preserve. Do not invest in incrementally improving the hash
embedder — when RAG matters, swap in a real provider behind the existing interface.

### 3. The CWD-relative path bug reaches the static mount too

Issue #21 catalogs six CWD-relative seed/source path sites. `app/main.py:95` adds a
seventh that is arguably the most visible:

```python
app.mount("/static", StaticFiles(directory="app/static"), name="static")
```

`directory="app/static"` resolves against the process working directory. Launched
from the repo root it works; launched from anywhere else, every static asset
(dashboard CSS, JS, and the index it references) 404s. This belongs on the #21 fix
list. The correct pattern is the file-anchored form already used elsewhere in the
repo (`Path(__file__).resolve().parents[…] / "app" / "static"`).

This strengthens the #21 thesis: the perceived emptiness and breakage of the
dashboard is substantially a **launch-directory** problem, not a content or feature
problem.

### 4. Schema surface is large relative to backing logic

There are ~50 schema modules in `app/schemas/`. Much of this is justified by the
breadth of advisory products, but a few (`chatgpt_surface.py`, `data_tools.py`,
`staff_updates.py` vs `staff_products.py`) suggest accreted surfaces from earlier
product directions that may no longer be load-bearing. Not urgent, but during the
agent-retirement cleanup (#8) it is worth checking whether any schema modules are
now orphaned — schemas with no importing route or service are pure carrying cost.

## Scope & ROI Read (the altitude take)

The project's genuine spine is three things:
1. **Advisory agents** — the staff/MOS/section advisor layer. This is real, broad,
   and the differentiated value. (It is also slightly over-grown; #8 trims it.)
2. **JSON file-store continuity** — handoffs, actions, travel cases, battle rhythm.
   This is the "survives between drills" value and it actually works.
3. **The dashboard** — the operator surface that ties 1 and 2 together.

Everything else is either supporting (ingestion/feeds, which work) or aspirational
scaffolding carried as if active (the DB and RAG layers). The highest-leverage move
is not to build more — it is to **stop the running app from presenting as broken**:

- Fix the path-bug classes (#1 startup storage, #21 seed/source, and the static
  mount above). Combined these are well under ~30 lines and likely convert the app
  from "won't launch / empty panels" to "launches and shows its existing content."
- Add one regression test that launches/loads from a non-root working directory.
  The 1,665-assertion suite is structurally blind to this entire bug class because
  pytest always runs from the repo root.
- Then make the DB and RAG decisions deliberately (cut-from-setup / relabel) so the
  project stops advertising and provisioning capabilities it does not have.

What to **not** invest in right now:
- New content for the history / reading / doctrine panels — the content exists; the
  path bug hides it (#21).
- New agents — the roster is already large; marginal value is low against
  orchestration and the path/auth fixes.
- Incremental RAG embedder improvement — it will be replaced wholesale.

## Cross-Reference

This pass adds architectural findings on top of the existing backlog. The
issue-level items remain in GitHub issues #1–#21. The two new decisions surfaced
here (vestigial DB, mislabeled RAG) and the static-mount path extension are not yet
filed as issues and are recorded here for the maintainer to triage.

---

# Pre-Upload Readability & Agent Consolidation Plan

Context: the repo is being prepared for upload to an external GitHub org for review
by competent engineers. The governing principle: **expert reviewers judge maturity
by signal-to-noise, honesty, and coherence — not by surface area.** The repo
currently optimizes for surface area (~90 registered agents, ~40 routes, 59 docs),
which a sharp reviewer reads as sprawl unless it is framed. Genuine strengths
(broad coherent domain model, ~1,665-assertion test suite, explicit safety posture,
local-first design) are real but currently buried under noise.

## Maximizing Human Readability

Reviewers evaluate outside-in and reach a verdict in minutes: README → directory
structure → a few representative files → tests → docs. Highest-leverage moves, in
order:

1. **Prune `docs/` ruthlessly before upload (biggest win, lowest effort).**
   `core_documents/` currently mixes six session-detritus files (two handoffs, a
   blocker note, offline notes, two dated feedback files) beside the authoritative
   `project_purpose.md` and `roadmap.md`. Session scratch next to authoritative docs
   signals "these people don't curate." Move dated handoffs/blockers/feedback/scratch
   into `docs/archive/` or off the review branch. Valuable to the maintainer; noise
   to a reviewer.
2. **Honesty in labeling beats breadth.** Experts forgive "this is a stub" instantly;
   they lose respect for "presented as working but isn't." Mark stubs as stubs in the
   capability table (RAG especially), and either cut the `init_db` setup step or
   annotate it as future-schema (see the vestigial-DB finding above). This converts
   credibility liabilities into evidence of self-awareness.
3. **Make the README setup work on first try.** Nothing erodes expert confidence
   faster than "I followed your README and it didn't launch." Fix the path bugs
   (#1, #21, and the static mount) before upload.
4. **Add one authoritative reviewer entry point** — an honest `ARCHITECTURE.md`
   naming the spine (advisory agents + JSON continuity stores + dashboard), the stubs
   (DB, RAG), the route map, and where to look first. One honest map beats 59
   scattered notes. (`CONTRIBUTING_QUICKSTART.md` and `workflow_map.md` already exist;
   verify they point a *reviewer*, not just a contributor, at the spine.)
5. **Frame the agent directory** so 49 files read as "one pattern, N instances," not
   "49 copy-pastes." A short header note explaining the `Agent` base + `source_refs`
   pattern turns apparent bloat into apparent discipline.

## Agent Consolidation — compile, shift, and cull

The reframe: it is not 49 files that is the problem — it is that (a) several "agents"
are boilerplate that should be *data*, and (b) three overlapping surfaces reach
similar advisory logic (`/agents/...`, `/training/...`, `/staff/...`), which reads as
architectural indecision. Current state: 49 agent files, ~7,062 LOC, ~90 registered
agents.

| Move | What | Effect |
|---|---|---|
| **Cull** | The 7 redundant agents in issue #8 | ~700 LOC + 7 registry entries gone, zero capability lost |
| **Compile to data** | The 8 MOS agents (0102, 0202, 0402, 0430, 0511, 3002, commo, civil-affairs) are near-identical "narrow MOS slice under parent staff lane X." Convert to data rows + the existing `ROLE_DEFINITIONS`-style builder | ~750 LOC of hand-written files → ~80 lines of data, using a pattern the repo already invented |
| **Collapse** | MCPP, R2P2, OPT-facilitator, assessment-learning are one "how do we run planning" advisor with modes | 4 files → 1 |
| **Trim registration** | Keep `staff_advisor_agent.py` and `ROLE_DEFINITIONS`, but only *register* used echelons (company + battalion, maybe regiment); generate higher echelons on demand. Cells like `staff-mef-g8` are never invoked | Registry surface ~90 → ~35 with zero capability deleted |
| **Shift to skills** | Workflow-shaped "agents" (value = procedure, not judgment-framing): `maradmin-monitor` is superseded by the `usmc-monitoring` skill; `chief-of-staff-aide` overlaps the `personal-chief-of-staff` skill | A few agents retire into existing skills |

**Net effect:** ~90 registered agents → ~30–35; 49 files → ~20; thousands of
boilerplate LOC → data tables. No genuine capability lost, and each remaining agent
has an obvious distinct job — which is what makes the directory legible.

**The test for agent vs. skill vs. tool:** if the value is judgment-framing, it is an
agent; if it is "orchestrate these routes in this order," it is a skill; if it is
deterministic generation, it is a route/service. Several current "agents"
(`staff-products`, `pki-cac-troubleshooter`) are really thin wrappers over
deterministic builders and could be reframed accordingly.

## Recommended pre-upload sequence

1. Prune `docs/` (first-impression win, lowest effort)
2. Fix the path bugs so it launches clean (#1, #21, static mount)
3. Honest capability/stub labeling (README + cut/annotate `init_db`)
4. Cull #8 + compile the 8 MOS agents to data (highest-ROI agent moves)
5. One `ARCHITECTURE.md` reviewer entry naming the spine and the stubs

Items 1–3 are judged in the first five minutes; 4–5 in the next thirty. The
staff-council registration trim and planning-cluster collapse are real but
lower-urgency and can follow.

---

# Delivery & Turn-Key Strategy

Goal: turn-key usage across three user tiers — (1) people with AI accounts who barely
use them, (2) regular AI users who are not coders, (3) AI-fluent deep divers. The key
strategic correction: **the dashboard/local app is not the turn-key surface for the
less-technical tiers, and trying to make it so fights the architecture.**

## The two governing facts

1. **The app does not call an LLM at runtime.** Agents return structured, templated
   advisory text. The reasoning is meant to come from the human's own AI (Claude /
   ChatGPT) consuming the repo's patterns, or from a person reading structured output.
   This is the correct design for an OPSEC context — but it means a novice who "has an
   AI account" and opens the dashboard experiences a forms-and-checklists tool, not
   generative AI. Set that expectation explicitly or it reads as a letdown.
2. **Running it requires Python, venv, pip, a terminal, and git** — and currently it
   will not launch cleanly (path bugs). That is the opposite of turn-key for anyone
   below Tier 3. Dashboard polish does not change the fact that *getting to* the
   dashboard is a developer task.

Conclusion: the local app is inherently a Tier-3 (and privacy-conscious Tier-2)
surface. The cheaper, higher-reach path to turn-key is to give Tiers 1 and 2 a
different vehicle entirely.

## Per-tier delivery

| Tier | Best vehicle | Build cost | Reasoning source |
|---|---|---|---|
| 1 — barely-AI | Hosted Claude Project / Custom GPT preloaded with the skills, reference notes, and safety rules. Zero install, works on a phone. They *talk to it*. | **Lowest** — curate + package existing skills/docs | Their AI account |
| 2 — regular AI | The same Project, used harder for product generation; the share-safe packet route (`/sharing/external-ai-packet`) bridges local context into their AI; optional packaged desktop app for those who want the structured drafting/continuity tools | Low / Medium | Their AI account |
| 3 — deep divers | The repo as it exists, once it launches clean and the docs are honest — connect Claude Code / Codex and extend | Already built | Connected AI + the human |

**The strategic inversion:** the assumed hierarchy is "dashboard for novices, repo for
experts." The reality that serves users best is closer to the inverse — two of three
tiers do not want software at all; they want a chat surface preloaded with the repo's
patterns. That surface is cheap to build *because the skills already exist.* The
unlock for Tiers 1–2 is **curation, not software** — which means the docs-pruning
work above is load-bearing for product strategy, not just reviewer optics (the same
curated bundle feeds the Project).

## Cross-cutting prerequisites

1. **Fix the path bugs first** (#1, #21, static mount). A packaged desktop app makes
   this *more* critical — the launch directory becomes unpredictable, so CWD-relative
   paths guarantee breakage.
2. **Decide the LLM-at-runtime question explicitly.** Recommendation: do *not* put an
   LLM in the local app. Keep the local app deterministic and private; let the hosted
   Project be the generative surface. One privacy story per surface, clearly labeled.
3. **Set expectations in the README:** "This is a structured staff-workflow tool; the
   AI reasoning comes from your connected assistant." One sentence prevents every
   "where's the AI?" disappointment.

## Recommended sequence

1. Finish the pre-upload cleanup (docs prune + path fixes + honest labels) — serves
   the review *and* becomes raw material for the Project.
2. Build the hosted Claude Project / Custom GPT from the curated skills + docs — the
   turn-key win for Tiers 1–2 at lowest cost, mostly assembly of existing pieces.
3. Document the share-safe-packet workflow as the bridge for privacy-conscious Tier-2.
4. Only then consider a packaged desktop app, gated on whether anyone actually asks
   for the local tool over the chat surface.

Headline: turn-key does not come from a friendlier dashboard. It comes from
recognizing that two of three tiers want a chat surface preloaded with the repo's
patterns — and building that, cheaply, from skills that already exist.
