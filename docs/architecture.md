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
- `app/services/agents`: Agent interface, registry, and placeholder agent implementations.
- `app/services/ingestion`: Public-source ingestion stubs for RSS/HTML, MCPEL manifests, and PDFs.
- `app/services/rag`: Chunking, embedding, vector-store, and retriever abstractions.
- `app/services/calendar`: Drill-prep planning and provider stubs.
- `app/services/org_awareness`: Unit hierarchy and exercise cadence support.
- `app/services/storage`: Local filesystem storage for user-provided working context.
- `app/services/billets`: Advisory SMCR billet recommendation from parsed public-source listings.

## Compatibility Guidance

Hosted-AI compatibility notes and repo-mode guidance live under `docs/compatibility/`.

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
