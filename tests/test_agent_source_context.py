import hashlib
from pathlib import Path

from app.schemas.agents import SourceSelection
from app.schemas.source_library import SavedSource
from app.schemas.source_state import VerifiedSourceStatus
from app.services.agents.source_context import SourceEvidenceResolver
from app.services.rag.chunking import TextChunk
from app.services.source_library.store import SourceLibraryStore


def test_resolver_combines_explicit_and_query_hits_without_duplicates(tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    explicit_id = _save_source(store, "owner", "source-explicit", "Bridge assessment", "Bridge access review")
    _save_source(store, "owner", "source-query", "Route study", "Bridge crossing condition")
    resolver = SourceEvidenceResolver(store)

    resolved = resolver.resolve("owner", SourceSelection(source_ids=[explicit_id], query="bridge"))

    assert len({item["chunk_id"] for item in resolved.items}) == len(resolved.items)
    assert resolved.items[0]["source_hash"]
    assert {item["title"] for item in resolved.items} == {"Bridge assessment", "Route study"}
    assert len(resolved.source_trust) == 2


def test_noncurrent_source_requires_explicit_opt_in(tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    watch_id = _save_source(
        store,
        "owner",
        "source-watch",
        "Watch source",
        "Bridge access review",
        trust_status=VerifiedSourceStatus.watch,
    )
    resolver = SourceEvidenceResolver(store)

    excluded = resolver.resolve("owner", SourceSelection(source_ids=[watch_id]))
    included = resolver.resolve("owner", SourceSelection(source_ids=[watch_id], include_noncurrent=True))

    assert not excluded.items and excluded.warnings
    assert included.items and any("non-current" in warning.lower() for warning in included.warnings)


def test_resolver_caps_combined_evidence_with_explicit_sources_first(tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    explicit_id = _save_source(
        store,
        "owner",
        "source-explicit",
        "Explicit source",
        "Bridge access review",
        chunks=["Bridge access review", "Additional bridge detail"],
    )
    _save_source(store, "owner", "source-query", "Query source", "Bridge crossing condition")
    resolver = SourceEvidenceResolver(store)

    resolved = resolver.resolve("owner", SourceSelection(source_ids=[explicit_id], query="bridge", limit=1))

    assert len(resolved.items) == 1
    assert resolved.items[0]["title"] == "Explicit source"


def test_resolver_rejects_sources_not_owned_by_user(tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    source_id = _save_source(store, "other-owner", "source-private", "Private source", "Bridge access review")
    resolver = SourceEvidenceResolver(store)

    try:
        resolver.resolve("owner", SourceSelection(source_ids=[source_id]))
    except ValueError as exc:
        assert "does not belong" in str(exc)
    else:
        raise AssertionError("Expected a foreign source selection to be rejected.")


def _save_source(
    store: SourceLibraryStore,
    user_key: str,
    source_id: str,
    title: str,
    text: str,
    *,
    trust_status: VerifiedSourceStatus = VerifiedSourceStatus.current,
    chunks: list[str] | None = None,
) -> str:
    source = SavedSource(
        source_id=source_id,
        user_key_digest="0" * 64,
        original_url=f"https://example.test/{source_id}",
        canonical_url=f"https://example.test/{source_id}",
        title=title,
        media_type="text/html",
        content_hash=hashlib.sha256(source_id.encode()).hexdigest(),
        byte_size=len(text),
        raw_content_path="",
        normalized_text_path="",
        chunks_path="",
        chunk_count=0,
        trust_status=trust_status,
    )
    chunk_texts = chunks or [text]
    saved = store.save(
        user_key,
        source,
        text.encode(),
        text,
        [TextChunk(chunk_index=index, text=chunk_text) for index, chunk_text in enumerate(chunk_texts)],
    )
    return saved.source_id
