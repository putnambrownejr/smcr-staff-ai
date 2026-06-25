# Roadmap

Honest current-state roadmap. For the architectural map of what is real vs. stub,
see [ARCHITECTURE.md](../../ARCHITECTURE.md).

---

## Shipped

These are implemented, tested, and in active use.

- **Advisory agent layer** — 35 agents: 19 standalone advisors + 16 echelon-adaptive
  staff archetypes (platoon → division/group). Includes MAGTF elements (ACE/GCE/LCE),
  functional advisors (ORM, OSINT, PKI, red-team, writing/briefing, uniform, drill prep),
  and MOS-specific advisors (infantry 03xx, artillery 08xx, custom MOS recipes).
- **JSON file-store continuity** — handoffs, actions/POAMs, travel cases, battle
  rhythm, section memory, opportunities, drill plans. Survives between drills.
- **Dashboard** — single-page operator surface with lane navigation, readiness
  posture, Act Now queue, source watch, and workflow tools.
- **Chief of Staff / Aide brief** — orchestrates handoff + documents + drill +
  career + actions into a daily/drill-period brief.
- **MARADMIN / message ingestion** — RSS/print-view parsing, message-watch
  feeds (NAVADMIN/ALNAV/DoD), custom watch feeds, source hashing.
- **SMCR billet discovery** — public BIC parsing and MOS/rank/location ranking.
- **Admin workflows** — DTS, GTCC, MROWS rebuttal, RIDT scaffolds.
- **Staff products** — WARNO/OPORD/FRAGO/SITREP/AAR and correspondence scaffolds.
- **Portable knowledge docs** — doctrine reference, echelon guide, and agent
  contributor guide extracted to `docs/` for tool-agnostic use.
- **Safety posture** — UNCLASSIFIED enforcement, PII detection + redaction,
  sensitive-content refusal, local-first storage, API-key gating.
- **MOS advisor expansion** — added 0602 CommO, 4402 JAG, and 7200 Aviation
  Wing advisor specs.
- **Seeded reference data** — history facts now include 29 entries with a
  randomizer fallback, and the Commandant's reading list is seeded with 13 books.
- **Doctrine source manifest** — populated public-source doctrine links across
  the source categories for official public ingestion metadata.
- **CI and dependency hygiene** — ruff zero-error enforcement runs in CI, with
  `uv.lock` and Dependabot configured for dependency update flow.

## Stub / Interface-Only

Real interfaces, no production implementation. See ARCHITECTURE.md for detail.

- **RAG over doctrine** — chunking/embedding/vector-store interfaces exist, but
  the embedder is a hash stub and the store does lexical overlap, not semantic
  retrieval. A real provider replaces both behind the interface when this becomes
  a priority. Do not invest in incrementally improving the hash embedder.
- **SQLite database** — five tables defined but unused at runtime; all live state
  is JSON file stores. Kept as a documented future doctrine-ingestion schema.
- **Live calendar / email connectors** — Microsoft Graph and Google Calendar
  interfaces are stubs. Local ICS export works. The `connector-adapter` skill
  handles normalization of externally-collected data without OAuth ownership.

## Current Priorities

The active focus, in order:

1. **Pre-release readiness** — honest docs, clean first-run launch, path-bug and
   auth fixes for external review (FHG AI initiative upload).
2. **Continuity between drills** — the file-store layer is the differentiated
   value; keep deepening handoff → brief → action workflow bridges.
3. **Thin-bench / lone-planner support** — the most common real use case.
4. **Discoverability** — quickstart, workflow map, skill catalog, honest
   architecture entry point so reviewers and contributors find the spine fast.
5. **Turn-key delivery for non-technical tiers** — a hosted Claude Project /
   Custom GPT preloaded with the skills and reference notes reaches users who
   want a chat surface, not a local install. (See the delivery strategy in the
   archived June assessment.)

## Deliberately Not Prioritized

- More specialist agents — the roster is already broad; marginal value is low
  against orchestration and packaging.
- Incremental RAG embedder improvement — it will be replaced wholesale.
- An LLM inside the local app — the local app stays deterministic and private;
  generative reasoning comes from the user's connected AI assistant.
- Docker / hosted MCP surfaces — maintained as secondary, not leading items.

## Governance (future)

- Formal security reporting, contributor policy, and release process for public
  GitHub distribution.
- Controlled UNCLASSIFIED unit pilot with example data and feedback capture.
- Generalization of org models and source manifests for broader reserve use.
