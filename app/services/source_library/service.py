"""Orchestration for approved, local public-source records."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.agents import Confidence, StructuredCitation
from app.schemas.source_library import (
    SavedSource,
    SourceFetchApproval,
    SourceFetchPreview,
    SourceFetchRequest,
    SourceRetrieveRequest,
    SourceRetrieveResponse,
    SourceRetrieveResult,
)
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.rag.chunking import chunk_text
from app.services.source_library.fetcher import PublicSourceFetcher
from app.services.source_library.store import SourceLibraryStore


class SourceLibraryPreviewRequest(BaseModel):
    user_key: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2_048)
    title: str | None = Field(default=None, max_length=500)
    publisher: str | None = Field(default=None, max_length=500)

    def source_request(self) -> SourceFetchRequest:
        return SourceFetchRequest(url=self.url, title=self.title, publisher=self.publisher)


class SourceLibraryFetchRequest(BaseModel):
    user_key: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2_048)
    title: str | None = Field(default=None, max_length=500)
    publisher: str | None = Field(default=None, max_length=500)
    preview: SourceFetchPreview
    approval: SourceFetchApproval

    def source_request(self) -> SourceFetchRequest:
        return SourceFetchRequest(url=self.url, title=self.title, publisher=self.publisher)


class SourceLibraryRecheckRequest(BaseModel):
    user_key: str = Field(min_length=1, max_length=500)
    preview: SourceFetchPreview | None = None
    approval: SourceFetchApproval | None = None


class SourceLibraryReviewRequest(BaseModel):
    user_key: str = Field(min_length=1, max_length=500)
    status: VerifiedSourceStatus
    notes: str | None = Field(default=None, max_length=2_000)


class SourceRecheckResult(BaseModel):
    source: SavedSource
    content_changed: bool
    candidate_hash: str


class SourceLibraryService:
    """Coordinates preview, approved fetching, storage, trust review, and retrieval."""

    def __init__(self, store: SourceLibraryStore, fetcher: PublicSourceFetcher) -> None:
        self._store = store
        self._fetcher = fetcher

    def preview(self, request: SourceLibraryPreviewRequest) -> SourceFetchPreview:
        return self._fetcher.build_preview(request.user_key, request.source_request())

    def fetch(self, request: SourceLibraryFetchRequest) -> SavedSource:
        fetched = self._fetcher.fetch_approved(
            request.user_key, request.source_request(), request.approval, request.preview
        )
        source = SavedSource(
            source_id=uuid4().hex,
            user_key_digest=self._store.user_key_digest(request.user_key),
            original_url=request.url,
            canonical_url=fetched.canonical_url,
            title=fetched.title,
            publisher=request.publisher,
            media_type=fetched.media_type,
            content_hash=fetched.content_hash,
            byte_size=fetched.byte_size,
            raw_content_path="",
            normalized_text_path="",
            chunks_path="",
            chunk_count=0,
        )
        return self._store.save(
            request.user_key, source, fetched.raw_bytes, fetched.normalized_text, chunk_text(fetched.normalized_text)
        )

    def list(self, user_key: str) -> list[SavedSource]:
        return self._store.list(user_key)

    def retrieve(self, request: SourceRetrieveRequest) -> SourceRetrieveResponse:
        results = []
        for hit in self._store.search(request.user_key, request.query, request.source_ids, request.limit):
            source = hit.source
            results.append(
                SourceRetrieveResult(
                    excerpt=hit.chunk.text,
                    citation=StructuredCitation(
                        title=source.title,
                        url=source.canonical_url,
                        publisher=source.publisher,
                        retrieved_at=source.retrieved_at.isoformat(),
                        source_hash=source.content_hash,
                        document_version=source.document_version,
                        effective_date=source.effective_date,
                        page=hit.chunk.page_number,
                        paragraph=hit.chunk.paragraph_index,
                        chunk_id=f"{source.source_id}:{hit.chunk.chunk_index}",
                        confidence=Confidence.low,
                        notes="Locally retained public source; verify trust status before use.",
                    ),
                    source_trust=SourceTrustMarker(
                        tracked_title=source.title,
                        status=source.trust_status,
                        verification_source_url=source.canonical_url,
                        last_verified_at=source.last_rechecked_at,
                        notes=source.review_notes,
                    ),
                )
            )
        return SourceRetrieveResponse(results=results)

    def recheck_preview(self, user_key: str, source_id: str) -> SourceFetchPreview | None:
        source = self._store.get(user_key, source_id)
        if source is None:
            return None
        return self._fetcher.build_preview(user_key, self._fetch_request(source))

    def recheck(self, source_id: str, request: SourceLibraryRecheckRequest) -> SourceRecheckResult | None:
        source = self._store.get(request.user_key, source_id)
        if source is None or request.preview is None or request.approval is None:
            return None
        fetched = self._fetcher.fetch_approved(
            request.user_key, self._fetch_request(source), request.approval, request.preview
        )
        changed = fetched.content_hash != source.content_hash
        status = VerifiedSourceStatus.watch if changed else source.trust_status
        updated = source.model_copy(
            update={
                "trust_status": status,
                "last_rechecked_at": datetime.now(UTC),
                "review_notes": (
                    "A recheck found changed content. The retained local copy was not replaced; review the source."
                    if changed
                    else source.review_notes
                ),
            }
        )
        saved = self._replace_metadata(request.user_key, updated)
        return SourceRecheckResult(source=saved, content_changed=changed, candidate_hash=fetched.content_hash)

    def review(self, source_id: str, request: SourceLibraryReviewRequest) -> SavedSource | None:
        source = self._store.get(request.user_key, source_id)
        if source is None:
            return None
        if request.status not in {VerifiedSourceStatus.current, VerifiedSourceStatus.superseded}:
            raise ValueError("Human review may set source trust only to current or superseded.")
        return self._replace_metadata(
            request.user_key,
            source.model_copy(
                update={"trust_status": request.status, "review_notes": request.notes, "last_rechecked_at": datetime.now(UTC)}
            ),
        )

    def remove(self, user_key: str, source_id: str) -> bool:
        return self._store.remove(user_key, source_id)

    @staticmethod
    def _fetch_request(source: SavedSource) -> SourceFetchRequest:
        return SourceFetchRequest(url=source.original_url, title=source.title, publisher=source.publisher)

    def _replace_metadata(self, user_key: str, source: SavedSource) -> SavedSource:
        """Rewrite metadata while preserving the retained immutable local source copy."""
        user_root = (self._store.root_dir / self._store.user_key_digest(user_key)).resolve()
        raw_path = (user_root / source.raw_content_path).resolve()
        text_path = (user_root / source.normalized_text_path).resolve()
        if not raw_path.is_relative_to(user_root) or not text_path.is_relative_to(user_root):
            raise ValueError("Source-library path escapes user storage.")
        return self._store.save(
            user_key,
            source,
            raw_path.read_bytes(),
            text_path.read_text(encoding="utf-8"),
            self._store._read_chunks(user_key, source),  # noqa: SLF001 - store owns source chunk format
        )
