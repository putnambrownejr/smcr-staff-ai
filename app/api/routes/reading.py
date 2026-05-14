from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.reading import ReadingListBook, ReadingListBookSummary, ReadingListSource
from app.services.reading.catalog import ReadingListCatalogService

router = APIRouter(prefix="/reading-list", tags=["professional reading"])

SEED_DIR = Path(__file__).resolve().parents[3] / "data" / "seed"


@lru_cache
def reading_catalog() -> ReadingListCatalogService:
    return ReadingListCatalogService.from_yaml(SEED_DIR / "reading_list.example.yaml")


@router.get("/sources", response_model=list[ReadingListSource])
def list_reading_sources() -> list[ReadingListSource]:
    return reading_catalog().catalog.sources


@router.get("/books", response_model=list[ReadingListBook])
def list_reading_books(category: str | None = None, open_source_only: bool = False) -> list[ReadingListBook]:
    return reading_catalog().list_books(category=category, open_source_only=open_source_only)


@router.get("/books/{slug}/summary", response_model=ReadingListBookSummary)
def summarize_reading_book(slug: str) -> ReadingListBookSummary:
    summary = reading_catalog().summarize_book(slug)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Unknown reading-list book: {slug}")
    return summary
