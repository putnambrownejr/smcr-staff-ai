from pathlib import Path

from app.schemas.ingestion import MessageRecord

MAX_FEED_ENTRIES = 200


class MaradminFeedStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save_many(self, records: list[MessageRecord]) -> list[MessageRecord]:
        for record in records:
            self._path(record.source_id).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        self._trim_entries()
        return self.list(limit=len(records))

    def list(self, limit: int | None = None) -> list[MessageRecord]:
        records = [
            MessageRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob("*.json"))
        ]
        records.sort(
            key=lambda record: record.published_at or record.retrieved_at,
            reverse=True,
        )
        return records[:limit] if limit is not None else records

    def get(self, source_id: str) -> MessageRecord | None:
        path = self._path(source_id)
        if not path.exists():
            return None
        return MessageRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def _trim_entries(self) -> None:
        records_with_paths = [
            (MessageRecord.model_validate_json(path.read_text(encoding="utf-8")), path)
            for path in sorted(self.root_dir.glob("*.json"))
        ]
        if len(records_with_paths) <= MAX_FEED_ENTRIES:
            return

        if any(record.published_at or record.retrieved_at for record, _ in records_with_paths):
            records_with_paths.sort(
                key=lambda item: item[0].published_at or item[0].retrieved_at,
                reverse=True,
            )
            paths_to_delete = [path for _, path in records_with_paths[MAX_FEED_ENTRIES:]]
        else:
            paths_to_delete = [path for _, path in records_with_paths[:-MAX_FEED_ENTRIES]]

        for path in paths_to_delete:
            path.unlink()

    def _path(self, source_id: str) -> Path:
        safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in source_id)
        return self.root_dir / f"{safe_id}.json"
