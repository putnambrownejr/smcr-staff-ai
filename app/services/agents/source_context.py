"""Resolve approved local Source Library content into bounded agent evidence."""

from __future__ import annotations

from app.schemas.agents import ResolvedSourceEvidence, SourceSelection
from app.schemas.source_library import SavedSource, SourceLifecycle
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.source_library.store import SourceLibrarySearchHit, SourceLibraryStore


class SourceEvidenceResolver:
    """Converts user-owned Source Library chunks into normalized local evidence.

    This resolver never fetches content.  It reads only an already-retained source
    under the supplied user key and makes non-current trust states explicit.
    """

    def __init__(self, store: SourceLibraryStore) -> None:
        self._store = store

    def resolve(self, user_key: str, selection: SourceSelection) -> ResolvedSourceEvidence:
        if not user_key.strip():
            raise ValueError("Source selection requires a user_key.")

        sources = self._explicit_sources(user_key, selection.source_ids)
        items: list[dict[str, str]] = []
        source_trust: list[SourceTrustMarker] = []
        warnings: list[str] = []
        seen_chunk_ids: set[str] = set()
        seen_source_ids: set[str] = set()

        for source in sources:
            if len(items) >= selection.limit:
                break
            self._add_source(
                user_key,
                source,
                selection,
                items,
                source_trust,
                warnings,
                seen_chunk_ids,
                seen_source_ids,
            )

        if selection.query and len(items) < selection.limit:
            for hit in self._store.search(user_key, selection.query, None, selection.limit):
                self._add_hit(
                    hit,
                    selection,
                    items,
                    source_trust,
                    warnings,
                    seen_chunk_ids,
                    seen_source_ids,
                )

        return ResolvedSourceEvidence(items=items, source_trust=source_trust, warnings=list(dict.fromkeys(warnings)))

    def _explicit_sources(self, user_key: str, source_ids: list[str]) -> list[SavedSource]:
        sources: list[SavedSource] = []
        seen_ids: set[str] = set()
        for source_id in source_ids:
            if source_id in seen_ids:
                continue
            seen_ids.add(source_id)
            source = self._store.get(user_key, source_id)
            if source is None:
                raise ValueError("Selected source is unavailable or does not belong to this user.")
            sources.append(source)
        return sources

    def _add_source(
        self,
        user_key: str,
        source: SavedSource,
        selection: SourceSelection,
        items: list[dict[str, str]],
        source_trust: list[SourceTrustMarker],
        warnings: list[str],
        seen_chunk_ids: set[str],
        seen_source_ids: set[str],
    ) -> None:
        if not self._eligible(source, selection, warnings):
            return
        self._add_trust(source, source_trust, seen_source_ids)
        for chunk in self._store._read_chunks(user_key, source):  # noqa: SLF001 - store owns its chunk format
            if len(items) >= selection.limit:
                break
            chunk_id = f"{source.source_id}:{chunk.chunk_index}"
            if chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(chunk_id)
            items.append(self._item(source, chunk_id, chunk.text))

    def _add_hit(
        self,
        hit: SourceLibrarySearchHit,
        selection: SourceSelection,
        items: list[dict[str, str]],
        source_trust: list[SourceTrustMarker],
        warnings: list[str],
        seen_chunk_ids: set[str],
        seen_source_ids: set[str],
    ) -> None:
        if not self._eligible(hit.source, selection, warnings):
            return
        if len(items) >= selection.limit:
            return
        self._add_trust(hit.source, source_trust, seen_source_ids)
        chunk_id = f"{hit.source.source_id}:{hit.chunk.chunk_index}"
        if chunk_id in seen_chunk_ids:
            return
        seen_chunk_ids.add(chunk_id)
        items.append(self._item(hit.source, chunk_id, hit.chunk.text))

    @staticmethod
    def _eligible(source: SavedSource, selection: SourceSelection, warnings: list[str]) -> bool:
        if source.lifecycle is not SourceLifecycle.active:
            warnings.append(f"Source '{source.title}' is not active and was excluded.")
            return False
        if source.trust_status is VerifiedSourceStatus.current:
            return True
        if not selection.include_noncurrent:
            warnings.append(f"Non-current source '{source.title}' was excluded; opt in to include it.")
            return False
        warnings.append(f"Non-current source '{source.title}' was included with an explicit opt-in.")
        return True

    @staticmethod
    def _add_trust(source: SavedSource, source_trust: list[SourceTrustMarker], seen_source_ids: set[str]) -> None:
        if source.source_id in seen_source_ids:
            return
        seen_source_ids.add(source.source_id)
        source_trust.append(
            SourceTrustMarker(
                tracked_title=source.title,
                status=source.trust_status,
                verification_source_url=source.canonical_url,
                last_verified_at=source.last_rechecked_at,
                notes=source.review_notes,
            )
        )

    @staticmethod
    def _item(source: SavedSource, chunk_id: str, excerpt: str) -> dict[str, str]:
        return {
            "title": source.title,
            "publisher": source.publisher or "",
            "url": source.canonical_url,
            "retrieved_at": source.retrieved_at.isoformat(),
            "source_hash": source.content_hash,
            "chunk_id": chunk_id,
            "excerpt": excerpt,
            "trust_status": source.trust_status.value,
        }
