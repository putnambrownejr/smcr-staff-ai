from pathlib import Path

from app.services.reading.catalog import ReadingListCatalogService


def test_reading_catalog_loads_open_source_classics() -> None:
    service = ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml"))
    open_books = service.list_books(open_source_only=True)
    slugs = {book.slug for book in open_books}

    assert "defence-of-duffers-drift" in slugs
    assert "art-of-war" in slugs


def test_reading_catalog_summarizes_duffers_drift() -> None:
    service = ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml"))
    summary = service.summarize_book("defence-of-duffers-drift")

    assert summary is not None
    assert summary.book.open_source_available is True
    assert "small-unit tactics" in summary.book.key_themes
    assert any("gutenberg.org" in citation for citation in summary.citations)
