# Roadmap

Honest current-state roadmap. For the architectural map of what is real vs. stub,
see [ARCHITECTURE.md](../../ARCHITECTURE.md).

---

## Shipped

These are implemented, tested, and in active use.

- **Advisory agent layer** — ~30 agent files covering S/G-staff lanes, MOS slices
  (0102/0202/0402/0430/0511/3002/CommO/Civil Affairs, compiled to data), staff
  council echelons (company → division/group), and functional advisors (ORM, OSINT, PKI,
  red-team, writing/briefing, uniform, drill prep, privacy hygiene).
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
- **Skill layer** — 9 operator skills steering AI tools toward existing routes.
- **Safety posture** — UNCLASSIFIED enforcement, PII detection + redaction,
  sensitive-content refusal, local-first storage, API-key gating.

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
