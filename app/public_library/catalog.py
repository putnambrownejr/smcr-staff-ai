"""Search an explicitly published snapshot, never runtime directories or user data."""

import re
from pathlib import Path

from app.public_library.models import CatalogSnapshot, Category, LibraryItem, SearchItem, SearchResults

SNAPSHOT_PATH = Path(__file__).with_name("catalog.json")


class PublicCatalog:
    def __init__(self, snapshot: CatalogSnapshot) -> None:
        self._items = {item.id: item for item in snapshot.items}
        if len(self._items) != len(snapshot.items):
            raise ValueError("Duplicate public catalog IDs.")

    @classmethod
    def load(cls, path: Path = SNAPSHOT_PATH) -> "PublicCatalog":
        return cls(CatalogSnapshot.model_validate_json(path.read_text(encoding="utf-8")))

    def get(self, item_id: str) -> LibraryItem:
        try:
            return self._items[item_id]
        except KeyError:
            raise ValueError("Unknown library ID. Search the catalog for a valid ID.") from None

    def search(
        self, query: str = "", category: Category | None = None, limit: int = 12, offset: int = 0,
    ) -> SearchResults:
        if len(query) > 200 or not 1 <= limit <= 30 or not 0 <= offset <= 10000:
            raise ValueError("Use a query up to 200 characters, limit 1–30, and offset 0–10000.")
        words = re.findall(r"\w+", query.casefold())
        ranked: list[tuple[int, LibraryItem]] = []
        for item in self._items.values():
            if category is not None and item.category != category:
                continue
            title = item.title.casefold()
            searchable = f"{title} {item.summary} {item.content}".casefold()
            if all(word in searchable for word in words):
                ranked.append((sum(3 if word in title else 1 for word in words), item))
        ranked.sort(key=lambda row: (-row[0], row[1].title))
        selected = ranked[offset:offset + limit]
        return SearchResults(
            items=[SearchItem.model_validate(item.model_dump()) for _, item in selected],
            total=len(ranked), offset=offset,
            next_offset=offset + limit if offset + limit < len(ranked) else None,
        )
