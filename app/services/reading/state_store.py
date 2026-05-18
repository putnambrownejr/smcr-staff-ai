from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.reading import ReadingListBook
from app.schemas.reading_state import (
    ReadingProgressListResponse,
    ReadingProgressRecord,
    ReadingProgressStatus,
    UpsertReadingProgressRequest,
)


class ReadingProgressStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def list(self, user_key: str) -> ReadingProgressListResponse:
        records = [
            ReadingProgressRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob(f"{_prefix(user_key)}-*.json"))
        ]
        records.sort(key=lambda record: record.last_updated, reverse=True)
        return ReadingProgressListResponse(user_key=user_key, records=records)

    def get(self, user_key: str, slug: str) -> ReadingProgressRecord | None:
        path = self._path(user_key, slug)
        if not path.exists():
            return None
        return ReadingProgressRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def upsert(
        self,
        user_key: str,
        book: ReadingListBook,
        request: UpsertReadingProgressRequest,
    ) -> ReadingProgressRecord:
        record = ReadingProgressRecord(
            user_key=user_key,
            slug=book.slug,
            title=book.title,
            author=book.author,
            status=request.status,
            notes=request.notes,
            completed_at=request.completed_at if request.status == ReadingProgressStatus.completed else None,
            last_updated=datetime.now(UTC),
        )
        self._path(user_key, book.slug).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def _path(self, user_key: str, slug: str) -> Path:
        return self.root_dir / f"{_prefix(user_key)}-{_slug_hash(slug)}.json"


def _prefix(user_key: str) -> str:
    return hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:12]


def _slug_hash(slug: str) -> str:
    return hashlib.sha256(slug.encode("utf-8")).hexdigest()[:12]
