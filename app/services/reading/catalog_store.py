from pathlib import Path

from app.schemas.reading import ReadingListCatalog, ReadingListCatalogSnapshot


class ReadingListCatalogStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_path = self.root_dir / "current_catalog.json"

    def get(self) -> ReadingListCatalogSnapshot | None:
        if not self.snapshot_path.exists():
            return None
        return ReadingListCatalogSnapshot.model_validate_json(self.snapshot_path.read_text(encoding="utf-8"))

    def save(self, catalog: ReadingListCatalog, source_url: str) -> ReadingListCatalogSnapshot:
        snapshot = ReadingListCatalogSnapshot(source_url=source_url, catalog=catalog)
        self.snapshot_path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
        return snapshot
