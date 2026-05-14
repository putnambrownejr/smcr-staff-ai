from pathlib import Path

import yaml

from app.schemas.reading import ReadingListBook, ReadingListBookSummary, ReadingListCatalog

DEFAULT_READING_WARNINGS = [
    "Summaries are advisory study aids, not substitutes for reading the original work.",
    "For copyrighted works, store metadata and summaries only; do not commit full text.",
    "Verify current list membership against official Marine Corps University or MCA list pages.",
]


class ReadingListCatalogService:
    def __init__(self, catalog: ReadingListCatalog) -> None:
        self.catalog = catalog

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ReadingListCatalogService":
        with open(path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        return cls(ReadingListCatalog.model_validate(payload))

    def list_books(self, category: str | None = None, open_source_only: bool = False) -> list[ReadingListBook]:
        books = self.catalog.books
        if category:
            normalized = category.lower()
            books = [book for book in books if normalized in {item.lower() for item in book.categories}]
        if open_source_only:
            books = [book for book in books if book.open_source_available]
        return books

    def get_book(self, slug: str) -> ReadingListBook | None:
        for book in self.catalog.books:
            if book.slug == slug:
                return book
        return None

    def summarize_book(self, slug: str) -> ReadingListBookSummary | None:
        book = self.get_book(slug)
        if book is None:
            return None
        return ReadingListBookSummary(
            book=book,
            citations=book.source_urls,
            warnings=DEFAULT_READING_WARNINGS,
        )
