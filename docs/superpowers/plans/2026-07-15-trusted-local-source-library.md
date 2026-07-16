# Trusted Local Source Library Implementation Plan

> For agentic workers: execute task-by-task with fresh review gates and checkbox tracking.

**Goal:** Fetch a user-approved public HTML page or direct PDF once, retain it locally with trust/provenance metadata, and return cited local excerpts.

**Architecture:** Add source-library schemas, a user-key-scoped local store, a guarded direct-URL fetcher, a service, document routes, and then a dashboard panel. The fetch approval is specific to URL retrieval and does not use external LLM approval.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, httpx, BeautifulSoup4, pypdf, pytest, mypy, Ruff.

## Global Constraints

- Exact HTTP(S) URL only; no search, crawl, login, redirects, access-control bypass, private/loopback host, or network request before approval.
- Support HTML and direct PDF only. Stream no more than Settings.max_upload_bytes.
- Store user content and indexes locally, user-key scoped; do not write source copies to the repository.
- New sources start needs_review. Rechecks never silently replace content.
- Retrieval returns citation URL/title/publisher/retrieval time/hash/trust/chunk provenance, and filters inactive/non-UNCLASSIFIED sources.
- Include DRAFT — Verify all references against current official sources before acting. in every advisory result.

## File Structure

- Create app/schemas/source_library.py: fetch request/preview/approval, source record, lifecycle, retrieve models.
- Create app/services/source_library/store.py: user-key-scoped metadata, content, chunks, search, removal.
- Create app/services/source_library/fetcher.py: URL policy, preview/digest, approved one-request fetch, extraction, hashing.
- Create app/services/source_library/service.py: fetch/list/retrieve/recheck/review/remove orchestration.
- Modify app/core/config.py: source_library_storage_dir.
- Modify app/api/routes/documents.py: source-library endpoints.
- Modify app/static/dashboard/index.html and app/static/dashboard/dashboard.js: Source Library panel.
- Create tests/test_source_library.py and modify tests/test_documents_contract.py and tests/test_dashboard.py.

## Task 1: Add contracts and local configuration

**Files:**
- Create: app/schemas/source_library.py
- Modify: app/core/config.py
- Test: tests/test_source_library.py

**Interfaces:**
- Produces SourceFetchRequest, SourceFetchPreview, SourceFetchApproval, SavedSource, SourceRetrieveRequest, SourceRetrieveResponse.
- SourceFetchApproval has approval_digest, acknowledged, and acknowledged_finding_categories.
- Settings has source_library_storage_dir defaulting to default_local_context_dir() / "source_library".

- [ ] Step 1: Write failing tests

~~~python
def test_source_fetch_approval_requires_acknowledgement() -> None:
    with pytest.raises(ValidationError):
        SourceFetchApproval(approval_digest="a" * 64, acknowledged=False)

def test_source_library_storage_is_under_local_context() -> None:
    assert default_source_library_dir().name == "source_library"
~~~

- [ ] Step 2: Run uv run pytest tests/test_source_library.py -q
Expected: FAIL because source-library contracts do not exist.

- [ ] Step 3: Implement models

Define SourceLifecycle(active, stale, removed, rejected); SourceFetchPreview(url, host, expected_call_count=1, approval_digest, finding_categories, warnings); and SavedSource with source_id, user_key_digest, original_url, canonical_url, title, publisher, media_type, retrieved_at, content_hash, byte_size, lifecycle, VerifiedSourceStatus, local paths, chunk_count, and review_notes. SourceRetrieveResult contains excerpt, StructuredCitation, and SourceTrustMarker.

- [ ] Step 4: Run uv run pytest tests/test_source_library.py -q
Expected: PASS.

- [ ] Step 5: Commit

~~~bash
git add app/schemas/source_library.py app/core/config.py tests/test_source_library.py
git commit -m "feat: add source library contracts"
~~~

## Task 2: Persist isolated local copies and chunks

**Files:**
- Create: app/services/source_library/store.py
- Modify: tests/test_source_library.py

**Interfaces:**
- SourceLibraryStore(root_dir).save(user_key, source, raw_bytes, normalized_text, chunks)
- list(user_key), get(user_key, source_id), search(user_key, query, source_ids, limit), remove(user_key, source_id)

- [ ] Step 1: Write failing isolation/removal test

~~~python
def test_store_isolates_users_and_removes_content(tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    saved = store.save("user-a", source, b"<p>alpha</p>", "alpha", chunks)
    assert store.list("user-b") == []
    assert store.search("user-a", "alpha", None, 5)
    assert store.remove("user-a", saved.source_id) is True
    assert store.get("user-a", saved.source_id) is None
~~~

- [ ] Step 2: Run uv run pytest tests/test_source_library.py -q
Expected: FAIL because SourceLibraryStore is undefined.

- [ ] Step 3: Implement store

Use a SHA-256 user-key directory; write metadata JSON, raw body, normalized text, and chunk JSON below it. Lexical term-overlap search filters active and UNCLASSIFIED records. Every resolved path must remain below the user root. Removal deletes metadata/content/index files.

- [ ] Step 4: Run uv run pytest tests/test_source_library.py -q
Expected: PASS.

- [ ] Step 5: Commit

~~~bash
git add app/services/source_library/store.py tests/test_source_library.py
git commit -m "feat: persist local source library"
~~~

## Task 3: Add preview-bound exact-URL fetching

**Files:**
- Create: app/services/source_library/fetcher.py
- Modify: tests/test_source_library.py

**Interfaces:**
- PublicSourceFetcher(client_factory, max_bytes).build_preview(user_key, request)
- fetch_approved(user_key, request, approval, preview) returns raw bytes, normalized text, media type, title, hash, byte size, canonical URL.

- [ ] Step 1: Write failing MockTransport tests

~~~python
def test_fetcher_requires_matching_preview_before_one_html_request() -> None:
    preview = fetcher.build_preview("user-a", SourceFetchRequest(url="https://example.test/plan"))
    result = fetcher.fetch_approved("user-a", request, approved(preview), preview)
    assert result.normalized_text == "Plan Public text"
    assert result.content_hash
~~~

Cover PDF extraction plus rejection of file schemes, localhost, 127.0.0.1, RFC1918 hosts, redirects, unsupported types, oversize bodies, unapproved/stale digest, and CUI/non-UNCLASSIFIED labels.

- [ ] Step 2: Run uv run pytest tests/test_source_library.py -q
Expected: FAIL because PublicSourceFetcher is undefined.

- [ ] Step 3: Implement fetcher

Use urllib.parse and ipaddress to allow public HTTP(S) only. Use httpx.Client(follow_redirects=False), one GET, streaming byte limit, and reject a redirect. Parse HTML with BeautifulSoup(..., "html.parser").get_text(" ", strip=True); parse PDF using PdfReader(BytesIO(raw)); hash raw bytes with SHA-256.

- [ ] Step 4: Run uv run pytest tests/test_source_library.py -q
Expected: PASS.

- [ ] Step 5: Commit

~~~bash
git add app/services/source_library/fetcher.py tests/test_source_library.py
git commit -m "feat: fetch approved public sources"
~~~

## Task 4: Expose source-library and retrieval API

**Files:**
- Create: app/services/source_library/service.py
- Modify: app/api/routes/documents.py
- Modify: tests/test_documents_contract.py
- Modify: tests/test_source_library.py

**Interfaces:**
- POST /documents/source-library/preview
- POST /documents/source-library/fetch
- GET /documents/source-library
- POST /documents/source-library/retrieve
- POST /documents/source-library/{source_id}/recheck-preview
- POST /documents/source-library/{source_id}/recheck
- POST /documents/source-library/{source_id}/review
- DELETE /documents/source-library/{source_id}

- [ ] Step 1: Write failing API test

~~~python
def test_source_library_fetch_list_retrieve_and_remove(client: TestClient) -> None:
    preview = client.post("/documents/source-library/preview", json={"user_key": "u", "url": "https://example.test/a"})
    fetched = client.post("/documents/source-library/fetch", json=matching_fetch_payload(preview.json()))
    results = client.post("/documents/source-library/retrieve", json={"user_key": "u", "query": "public text"})
    deleted = client.delete(f"/documents/source-library/{fetched.json()['source_id']}?user_key=u")
    assert preview.status_code == fetched.status_code == results.status_code == deleted.status_code == 200
    assert results.json()["results"][0]["citation"]["source_hash"]
~~~

Assert initial needs_review, recheck hash difference becomes watch without replacement, only review changes trust to current/superseded, and another user gets 404.

- [ ] Step 2: Run uv run pytest tests/test_documents_contract.py tests/test_source_library.py -q
Expected: FAIL because service/routes do not exist.

- [ ] Step 3: Implement service/routes

Fetch saves needs_review source and chunks. Recheck stores a candidate and marks watch on changed hash; it never overwrites active text. Retrieval maps chunks to StructuredCitation and SourceTrustMarker. Return 409 missing/stale approval, 413 size, 415 media type, and 422 URL-policy/parse/classification rejection.

- [ ] Step 4: Run uv run pytest tests/test_documents_contract.py tests/test_source_library.py -q
Expected: PASS.

- [ ] Step 5: Commit

~~~bash
git add app/services/source_library/service.py app/api/routes/documents.py tests/test_documents_contract.py tests/test_source_library.py
git commit -m "feat: expose local source library"
~~~

## Task 5: Add dashboard panel and complete verification

**Files:**
- Modify: app/static/dashboard/index.html
- Modify: app/static/dashboard/dashboard.js
- Modify: tests/test_dashboard.py

- [ ] Step 1: Write failing bundle assertions

~~~python
def test_dashboard_bundle_has_source_library_controls() -> None:
    component_source = _decoded_dashboard_component_source()
    assert "Source Library" in component_source
    assert 'fetch("/documents/source-library/preview"' in component_source
    assert 'fetch("/documents/source-library/retrieve"' in component_source
~~~

- [ ] Step 2: Run uv run pytest tests/test_dashboard.py -q
Expected: FAIL because the panel does not exist.

- [ ] Step 3: Implement panel

Add a Workspace/Bench+Files Source Library card: exact URL/title/publisher inputs; preview/approval display; explicit fetch action; list with trust state/type/date; recheck/remove; and citation-bearing query results. Controls are labeled, keyboard reachable, and show loading/error/empty/stale states. URL entry alone never fetches.

- [ ] Step 4: Run focused checks

Run: uv run pytest tests/test_dashboard.py tests/test_documents_contract.py tests/test_source_library.py -q
Expected: PASS.

- [ ] Step 5: Run release checks and commit

Run: uv run pytest tests/ -q
Run: uv run mypy app tests
Run: uv run ruff check .

Expected: PASS except documented pre-existing unrelated failures.

~~~bash
git add app/static/dashboard/index.html app/static/dashboard/dashboard.js tests/test_dashboard.py
git commit -m "feat: add source library workspace panel"
~~~

## Plan Self-Review

Tasks 1–4 provide the approved exact-URL, durable local source, trust/recheck/removal, and provenance retrieval workflow. Task 5 adds no unapproved network action and only consumes tested routes. The plan excludes crawling, search, live planning agents, and external LLM inference.

## Execution Handoff

Plan complete and saved to docs/superpowers/plans/2026-07-15-trusted-local-source-library.md.

1. **Subagent-Driven (recommended)** — fresh agent per task with review gates.
2. **Inline Execution** — execute batches in this session with checkpoints.

Which approach?

