from __future__ import annotations

import builtins
import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from app.schemas.source_library import SavedSource, SourceLifecycle
from app.services.rag.chunking import TextChunk

_SOURCE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_TERM_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class SourceLibrarySearchHit:
    """A locally stored source chunk matched by lexical term overlap."""

    source: SavedSource
    chunk: TextChunk


class SourceLibraryStore:
    """Filesystem store for approved source copies, scoped by a user-key digest."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        user_key: str,
        source: SavedSource,
        raw_bytes: bytes,
        normalized_text: str,
        chunks: Iterable[TextChunk],
    ) -> SavedSource:
        """Write a source's metadata and local copies below its user's directory."""
        self._validate_user_key(user_key)
        self._validate_source_id(source.source_id)
        user_dir = self._user_dir(user_key)
        paths = self._paths(user_dir, source.source_id)
        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)

        materialized_chunks = builtins.list(chunks)
        saved = source.model_copy(
            update={
                "user_key_digest": self.user_key_digest(user_key),
                "raw_content_path": str(paths["raw"].relative_to(user_dir)),
                "normalized_text_path": str(paths["text"].relative_to(user_dir)),
                "chunks_path": str(paths["chunks"].relative_to(user_dir)),
                "chunk_count": len(materialized_chunks),
            }
        )
        paths["raw"].write_bytes(raw_bytes)
        paths["text"].write_text(normalized_text, encoding="utf-8")
        paths["chunks"].write_text(
            json.dumps([_serialize_chunk(chunk) for chunk in materialized_chunks], indent=2),
            encoding="utf-8",
        )
        paths["metadata"].write_text(saved.model_dump_json(indent=2), encoding="utf-8")
        return saved

    def list(self, user_key: str) -> builtins.list[SavedSource]:
        """Return sources belonging only to ``user_key``, newest first."""
        if not self._valid_user_key(user_key):
            return []
        metadata_dir = self._user_dir(user_key) / "metadata"
        if not metadata_dir.exists():
            return []
        sources = [source for path in metadata_dir.glob("*.json") if (source := self._read_source(path)) is not None]
        return sorted(sources, key=lambda source: source.retrieved_at, reverse=True)

    def get(self, user_key: str, source_id: str) -> SavedSource | None:
        if not self._valid_user_key(user_key) or not self._valid_source_id(source_id):
            return None
        return self._read_source(self._paths(self._user_dir(user_key), source_id)["metadata"])

    def search(
        self,
        user_key: str,
        query: str,
        source_ids: builtins.list[str] | None,
        limit: int,
    ) -> builtins.list[SourceLibrarySearchHit]:
        """Return active, UNCLASSIFIED chunks ranked by lexical query-term overlap."""
        if limit <= 0:
            return []
        query_terms = set(_terms(query))
        if not query_terms:
            return []
        allowed_ids = set(source_ids) if source_ids is not None else None
        hits: builtins.list[tuple[int, SourceLibrarySearchHit]] = []
        for source in self.list(user_key):
            if allowed_ids is not None and source.source_id not in allowed_ids:
                continue
            if not _is_retrievable(source):
                continue
            for chunk in self._read_chunks(user_key, source):
                overlap = len(query_terms.intersection(_terms(chunk.text)))
                if overlap:
                    hits.append((overlap, SourceLibrarySearchHit(source=source, chunk=chunk)))
        hits.sort(key=lambda item: (-item[0], item[1].source.retrieved_at, item[1].chunk.chunk_index))
        return [hit for _, hit in hits[:limit]]

    def remove(self, user_key: str, source_id: str) -> bool:
        """Delete a user's metadata, source body, normalized text, and chunk index."""
        if not self._valid_user_key(user_key) or not self._valid_source_id(source_id):
            return False
        user_dir = self._user_dir(user_key)
        paths = self._paths(user_dir, source_id)
        found = False
        for path in paths.values():
            if path.exists():
                path.unlink()
                found = True
        for directory in (user_dir / "metadata", user_dir / "raw", user_dir / "text", user_dir / "chunks", user_dir):
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
        return found

    @staticmethod
    def user_key_digest(user_key: str) -> str:
        return hashlib.sha256(user_key.encode("utf-8")).hexdigest()

    def _user_dir(self, user_key: str) -> Path:
        return self._resolve_below_root(self.root_dir / self.user_key_digest(user_key))

    def _paths(self, user_dir: Path, source_id: str) -> dict[str, Path]:
        return {
            "metadata": self._resolve_below_user(user_dir, "metadata", f"{source_id}.json"),
            "raw": self._resolve_below_user(user_dir, "raw", f"{source_id}.bin"),
            "text": self._resolve_below_user(user_dir, "text", f"{source_id}.txt"),
            "chunks": self._resolve_below_user(user_dir, "chunks", f"{source_id}.json"),
        }

    def _read_chunks(self, user_key: str, source: SavedSource) -> builtins.list[TextChunk]:
        if not self._valid_source_id(source.source_id):
            return []
        path = self._paths(self._user_dir(user_key), source.source_id)["chunks"]
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                return []
            return [_deserialize_chunk(item) for item in payload if isinstance(item, dict)]
        except (OSError, TypeError, ValueError):
            return []

    @staticmethod
    def _read_source(path: Path) -> SavedSource | None:
        try:
            return SavedSource.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _resolve_below_root(self, path: Path) -> Path:
        resolved_root = self.root_dir.resolve()
        resolved = path.resolve()
        if not resolved.is_relative_to(resolved_root):
            raise ValueError("Source-library path escapes storage root.")
        return resolved

    @staticmethod
    def _resolve_below_user(user_dir: Path, *parts: str) -> Path:
        resolved_user_dir = user_dir.resolve()
        candidate = (resolved_user_dir.joinpath(*parts)).resolve()
        if not candidate.is_relative_to(resolved_user_dir):
            raise ValueError("Source-library path escapes user storage.")
        return candidate

    @staticmethod
    def _valid_user_key(user_key: str) -> bool:
        return bool(user_key.strip())

    def _validate_user_key(self, user_key: str) -> None:
        if not self._valid_user_key(user_key):
            raise ValueError("Invalid user_key.")

    @staticmethod
    def _valid_source_id(source_id: str) -> bool:
        return bool(_SOURCE_ID_PATTERN.fullmatch(source_id))

    def _validate_source_id(self, source_id: str) -> None:
        if not self._valid_source_id(source_id):
            raise ValueError("Invalid source_id.")


def _serialize_chunk(chunk: TextChunk) -> dict[str, int | str | None]:
    return {
        "chunk_index": chunk.chunk_index,
        "text": chunk.text,
        "paragraph_index": chunk.paragraph_index,
        "page_number": chunk.page_number,
    }


def _deserialize_chunk(payload: dict[str, object]) -> TextChunk:
    chunk_index = payload.get("chunk_index")
    text = payload.get("text")
    paragraph_index = payload.get("paragraph_index")
    page_number = payload.get("page_number")
    if not isinstance(chunk_index, int) or not isinstance(text, str):
        raise ValueError("Invalid source-library chunk.")
    if paragraph_index is not None and not isinstance(paragraph_index, int):
        raise ValueError("Invalid source-library paragraph index.")
    if page_number is not None and not isinstance(page_number, int):
        raise ValueError("Invalid source-library page number.")
    return TextChunk(
        chunk_index=chunk_index,
        text=text,
        paragraph_index=paragraph_index,
        page_number=page_number,
    )


def _terms(text: str) -> builtins.list[str]:
    return _TERM_PATTERN.findall(text.lower())


def _is_retrievable(source: SavedSource) -> bool:
    return (
        source.lifecycle == SourceLifecycle.active
        and source.classification_label.strip().upper() == "UNCLASSIFIED"
        and not source.cui_flag
    )
