# Trusted Local Source Library and Retrieval Design

**Date:** 2026-07-15

**Status:** Approved

**Scope:** A durable, user-controlled local library for exact public HTML pages and direct PDFs, with preview-bound external fetching, trust state, local retrieval, and citation provenance. This is the first of two independent workstreams; planning-analysis agents are explicitly deferred until this foundation is delivered.

## Purpose

SMCR Staff AI currently validates source manifests and tracks source states, but its document listing endpoint is empty and its RAG vector store is in-memory. This release turns user-supplied public URLs into saved, reusable local sources that can later ground planning products without re-fetching or treating live web content as automatically current.

The design extends the accepted preview-and-approval approach for external processing to a distinct operation: fetching an exact URL. It does not use an external LLM, crawl the web, or make unchecked network calls.

## Global Constraints

- UNCLASSIFIED public sources only. Reject or quarantine any source labeled non-UNCLASSIFIED or CUI.
- Users submit exact public URLs only. The system does not search, crawl, follow links, authenticate, bypass access controls, paywalls, robots.txt, CAPTCHAs, or rate limits.
- Every fetch shows a preview and requires explicit operation-specific approval before network access. The preview identifies the exact URL, host, expected request count, intended local storage action, and sanitized metadata.
- Source copies, metadata, retrieval indexes, and audit records are local and user-key scoped. No user source content is committed to the repository.
- HTML and direct PDFs are supported. Unsupported media types, redirects to a different host/scheme, oversized responses, private-network addresses, or non-public URL schemes are rejected before storage.
- Source discovery, trust verification, and retrieval are separate. A successful fetch means only that a local copy exists; it does not establish accuracy, currency, authority, or applicability.
- Every retrieval result exposes provenance: source title, URL, publisher, retrieval time, source hash, version/effective date when available, trust state, and excerpt/chunk identifier.
- Every source-backed output remains advisory and includes: `DRAFT — Verify all references against current official sources before acting.`

## Existing Foundation and Gaps

The implementation reuses:

- `ExternalProcessingApproval` and its digest/acknowledgement pattern for explicit approval.
- `ExternalProcessingAuditLog` for metadata-only local auditing.
- `VerifiedSourceState` and source-update review concepts for trust status.
- `DocumentRead`, document chunking, structured citations, and `LocalRagPipeline` for normalized document/retrieval shapes.

The implementation replaces or extends these limitations:

- `POST /documents/ingest` is validation/dry-run only and cannot save a fetched URL.
- `GET /documents` returns an empty list.
- `IngestRequest` currently disallows a PDF URL.
- `LocalVectorStore` is process-memory only and the hash embedding provider is marked as a development stub.
- Existing source states do not represent a user-managed source library, local retained copy, removal lifecycle, or source content retrieval.

## Information Model

### Saved source

A saved source has:

- opaque source ID and user-key digest;
- original exact URL, normalized canonical URL, host, and media type;
- user-provided title/publisher plus extracted metadata when available;
- retrieval timestamp, HTTP response metadata allowed for local audit, content hash, byte size, and optional version/effective date;
- local content path and normalized text path;
- lifecycle state: active, stale, removed, or rejected;
- trust state: `needs_review` on first successful fetch, later `current`, `watch`, or `superseded` only through a review action;
- last verification/recheck timestamp and notes;
- chunk count and index version.

Removal deletes the local content/index records and retains only a minimal user-key-scoped audit event; it does not attempt to delete the public origin.

### Fetch preview and approval

A fetch request contains an exact HTTP(S) URL and optional user-supplied title/publisher. It returns a preview before any request that can retrieve content:

- operation scope `public-source-fetch`;
- exact URL, resolved host, intended media types, expected call count of one, size limit, and local-storage statement;
- sanitized user metadata and sensitive/PII detector findings;
- immutable approval digest binding URL, canonicalization policy, expected call count, user-key digest, and selected local storage action.

The existing disclosure modes do not authorize URL fetching. The source-library feature adds a fetch-specific approval model with `approved: true`, approval digest, and acknowledged finding categories. A stale digest, unacknowledged finding, host/scheme change, or redirect outside the approved exact/canonical URL scope requires a new preview.

### Retrieval

Source ingestion normalizes HTML/PDF text locally, chunks it, and writes records to a durable user-key-scoped local index. Retrieval accepts user key, text query, optional source IDs, and a limit. It filters to active, UNCLASSIFIED sources and returns local excerpts plus structured citations and trust markers.

The initial retrieval scoring may remain lexical if the existing local stub stays in place, but the API labels results as local retrieval and does not claim semantic relevance. The vector-store backend is behind an interface so a durable local backend can replace the stub without changing the API.

## API and Workflow

1. **Preview**: client submits an exact public URL to a source-library preview endpoint.
2. **Approve and fetch**: client submits the matching approval; server validates URL/scheme/host policy, fetches exactly once, checks response headers and size while streaming, stores local raw content plus normalized text, computes hash, creates source record with `needs_review`, and indexes chunks.
3. **List and inspect**: client lists its saved sources, reads source metadata, and views provenance/trust state.
4. **Retrieve**: client queries only its local active source library and receives excerpts with citations/trust state.
5. **Recheck**: client requests a new preview for the exact saved URL. A newly approved recheck compares hash/version metadata and marks a change as `watch` or `superseded`; it never silently replaces the saved source.
6. **Review**: user accepts or records a trust decision, updating the source's trust state.
7. **Remove**: client explicitly removes the local source and its index entries.

The dashboard surface is a Workspace/Bench+Files source-library panel. It shows source status, last retrieval/check date, source size/type, actions, and unambiguous empty/error states. It never displays a fetched source as doctrine or current policy solely because it was downloaded.

## Error and Safety Behavior

- Invalid schemes, localhost/private-network hosts, unsupported content type, oversized body, redirect, failed TLS/HTTP request, and malformed PDF/HTML return a precise non-storage failure.
- No content or metadata is stored if fetch approval is absent, stale, or mismatched.
- A successful response that appears non-UNCLASSIFIED or CUI is not indexed and is held only long enough to produce a rejection/audit event; the user must not be able to retrieve it.
- Parsing failure preserves the source metadata as rejected with a reason but does not create retrieval chunks.
- Empty source library returns an explicit local-library empty state and links to add a public source.
- Retrieval results with `needs_review`, `watch`, or `superseded` trust are visibly marked and do not become unqualified factual output.
- Sensitive/PII detector matches warn and require acknowledgement; they do not assert classification or override the user's legal handling judgment.

## Testing and Verification

Tests cover:

- preview/approval digest binding and the refusal of missing, stale, or mismatched approval;
- HTML and direct PDF happy paths with fixture responses, content hashing, local persistence, and retrieved citations;
- URL policy rejection for non-HTTP(S), private/loopback, redirect, unsupported content type, size limit, and non-UNCLASSIFIED/CUI content;
- user-key isolation for list, retrieve, recheck, and removal;
- first-ingest `needs_review` state, recheck change detection, explicit review transitions, and no silent replacement;
- source removal deleting local content and index entries;
- retrieval filtering to active, UNCLASSIFIED sources and carrying source hash/date/trust/chunk provenance;
- dashboard empty, loading, error, stale, and removal states;
- regression coverage for existing manifest validation, source state, document update, and external-processing behavior.

Before release:

~~~text
uv run pytest tests/ -q
uv run mypy app tests
uv run ruff check .
~~~

## Follow-on Planning-Analysis Release

After this source-library release, build a separate planning-capability specification and implementation plan. It will use the retrieved evidence envelope rather than direct web access:

1. Information Requirements Manager
2. Area Study Builder
3. Actor & Network Analyst
4. IPB Assistant
5. Red Team evidence and competing-hypotheses modes
6. Assessment/Learning source-backed lessons and applicability mode
7. Scenario Builder selected-source input with visibly synthetic output

The shared evidence envelope is: claim or excerpt, source/citation, retrieval date, source hash/version, trust state, confidence, label (`reported_fact`, `analytic_inference`, `planning_assumption`, or `synthetic_exercise_content`), and recommended validation action.

## Non-Goals

- Search-engine integration, web crawling, social-media monitoring, authenticated sites, or automated web discovery.
- Treating local retrieval as an intelligence collection capability.
- Source verification or freshness determination without explicit human review.
- Persistent planning products, area studies, actor profiles, or IPB records in this release.
- Targeting, infrastructure vulnerability analysis, individual profiling, or operationally sensitive inference.
- External LLM inference as part of source ingestion or retrieval.

DRAFT — Verify all references against current official sources before acting.

