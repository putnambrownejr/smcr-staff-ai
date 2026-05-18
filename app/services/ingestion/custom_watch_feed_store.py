from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.custom_watch_feeds import (
    CreateCustomWatchFeedRequest,
    CustomWatchFeed,
    UpdateCustomWatchFeedRequest,
)


class CustomWatchFeedStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.root_dir / "metadata"
        self.items_dir = self.root_dir / "items"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.items_dir.mkdir(parents=True, exist_ok=True)

    def create(self, request: CreateCustomWatchFeedRequest) -> CustomWatchFeed:
        feed_id = hashlib.sha256(f"{request.name}|{request.url}".encode()).hexdigest()[:16]
        now = datetime.now(UTC)
        record = CustomWatchFeed(
            feed_id=feed_id,
            name=request.name,
            url=request.url,
            category=request.category,
            trust_level=request.trust_level,
            enabled=request.enabled,
            tags=request.tags,
            created_at=now,
            updated_at=now,
        )
        self._write(record)
        return record

    def list(self) -> list[CustomWatchFeed]:
        records = [
            CustomWatchFeed.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.metadata_dir.glob("*.json"))
        ]
        records.sort(key=lambda record: record.updated_at, reverse=True)
        return records

    def get(self, feed_id: str) -> CustomWatchFeed | None:
        path = self._metadata_path(feed_id)
        if not path.exists():
            return None
        return CustomWatchFeed.model_validate_json(path.read_text(encoding="utf-8"))

    def update(self, feed_id: str, request: UpdateCustomWatchFeedRequest) -> CustomWatchFeed | None:
        record = self.get(feed_id)
        if record is None:
            return None
        update_data = request.model_dump(exclude_unset=True)
        updated = record.model_copy(update={**update_data, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def mark_refresh(
        self,
        feed_id: str,
        *,
        item_count: int,
        error: str | None,
    ) -> CustomWatchFeed | None:
        record = self.get(feed_id)
        if record is None:
            return None
        updated = record.model_copy(
            update={
                "updated_at": datetime.now(UTC),
                "last_refreshed_at": datetime.now(UTC),
                "last_error": error,
                "last_item_count": item_count,
            }
        )
        self._write(updated)
        return updated

    def delete(self, feed_id: str) -> bool:
        record = self.get(feed_id)
        if record is None:
            return False
        metadata_path = self._metadata_path(feed_id)
        if metadata_path.exists():
            metadata_path.unlink()
        items_path = self.items_path(feed_id)
        if items_path.exists():
            for child in items_path.glob("*"):
                child.unlink()
            items_path.rmdir()
        return True

    def items_path(self, feed_id: str) -> Path:
        return self.items_dir / feed_id

    def _metadata_path(self, feed_id: str) -> Path:
        return self.metadata_dir / f"{feed_id}.json"

    def _write(self, record: CustomWatchFeed) -> None:
        self._metadata_path(record.feed_id).write_text(
            record.model_dump_json(indent=2),
            encoding="utf-8",
        )
