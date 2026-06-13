# Architecture

The initial architecture is backend-first and intentionally modular.

## Primary Path

The primary product path is:

1. local FastAPI backend
2. local browser dashboard
3. local-only continuity, memory, and document storage

Older ChatGPT/MCP and Docker/container experiments have been removed. The repo should optimize for the direct local
backend + dashboard path first.

## Layers

- `app/api/routes`: FastAPI route handlers and request/response boundaries.
- `app/schemas`: Pydantic API contracts.
- `app/db`: SQLModel relational models and session setup. SQLite is the local default; Postgres is the target production-capable backend.
- `app/services/agents`: Agent interface, registry, and staff/MOS advisory implementations.
- `app/services/ingestion`: Public-source ingestion stubs for RSS/HTML, MCPEL manifests, and PDFs.
- `app/services/rag`: Chunking, embedding, vector-store, and retriever abstractions.
- `app/services/calendar`: Drill-prep planning and provider stubs.
- `app/services/org_awareness`: Unit hierarchy and exercise cadence support.
- `app/services/storage`: Local filesystem storage for user-provided working context.
- `app/services/billets`: Advisory SMCR billet recommendation from parsed public-source listings.
- `app/services/staff_products`: Advisory product scaffolds, section structures, and citation-grounded formatting logic.
- `app/services/staff`: Planning-cell, council, estimate, and battle-rhythm support workflows.
- `app/static/dashboard`: Local command-post style dashboard for continuity, watch functions, and workflow launch points.

## Compatibility Guidance

Hosted-AI compatibility notes and repo-mode guidance live under `docs/compatibility/`. Root-level
`AGENTS.md` and `.github/copilot-instructions.md` remain only as conventional discovery points for tools
that expect them there.

## RAG Direction

Documents retain source identifiers, publication metadata, classification labels, CUI flags, hashes, and chunk-level metadata. The local vector store is a deterministic stub so tests remain offline and reproducible. A future Chroma/Qdrant implementation should preserve the same service boundary.

`LocalRagPipeline` provides the first citation-preserving path from `DocumentRead` to chunks, vector records, retrieval results, and structured citations. The current implementation is local and lexical/deterministic; it exists to preserve contracts before a production vector database is introduced.

User-uploaded local context is stored separately and does not alter canonical document, doctrine, organization, exercise, or agent registry structure. Request models must explicitly name context IDs when a workflow should use local context.

Deep research planning artifacts are stored under `docs/deep_research/` and summarized under `docs/sources/`. They are
reference/planning material for ingestion design, not authoritative doctrine.

## Source Storage Strategy

For public doctrine and reading sources, the default repository artifact is a manifest entry plus a markdown synopsis/source note. Large PDFs, PPTX drill products, RQS/BIO files, and uncertain-copyright material should not be committed. They should be fetched from official locations at runtime or uploaded into ignored local storage with provenance, hash, and classification metadata.

## Safety Posture

The system is UNCLASSIFIED-only. Agents include allowed source lists, disallowed inputs, and human-review flags. Runtime guardrails detect likely sensitive inputs and force generic training/checklist style responses.

## Current Storage Architecture (as of 2026-06-12)

The actual storage layer is flat JSON, not SQLite or ORM. `database_url` and `vector_store_backend` are in Settings as reserved fields for future use — they are not wired to any code today.

Every persisted domain (session handoffs, section memory, bench sections, actions, reading state, etc.) uses the same pattern: `SHA256(user_key)[:24] → {digest}.json` under a dedicated subdirectory of `local_context/`. Each store is a standalone class that reads and writes one JSON blob per user key.

**MOS advisor agents** are frozen dataclass rows in `app/services/agents/mos_advisor.py`, not a dynamic registry. They are read-only and resolved at import time. If user-customizable agents are needed in the future, extend via a YAML override file in `local_context/` that the service merges on top of the defaults.

## Multi-User Extension Point

The `user_key` string is the isolation boundary for all stores. To support shared or multi-user workspaces without a full database migration:

- Introduce a `group_key` alongside `user_key` in stores that should be shared.
- Stores that are personal-only (`section_memory`, `bench_sections`, `handoffs`) reject group keys.
- Stores that support collaboration (`battle_rhythm`, `drill_plans`) accept either.
- The SHA256 path scheme works for both; group keys just need a distinct namespace (e.g. `grp_{key}`).
- Concurrent write safety would require file locking or migration to SQLite at that point.

Do not add `group_key` until a concrete shared-workspace use case exists.
