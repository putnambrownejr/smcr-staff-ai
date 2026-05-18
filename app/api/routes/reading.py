from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.reading import ReadingListBook, ReadingListBookSummary, ReadingListSource
from app.services.reading.catalog import ReadingListCatalogService
from app.services.reading.catalog_store import ReadingListCatalogStore
from app.services.reading.live_catalog import ReadingListRemoteCatalogService, load_effective_reading_catalog

router = APIRouter(prefix="/reading-list", tags=["professional reading"])

SEED_DIR = Path(__file__).resolve().parents[3] / "data" / "seed"


def get_catalog_store() -> ReadingListCatalogStore:
    return ReadingListCatalogStore(get_settings().reading_catalog_storage_dir)


def get_remote_catalog_service() -> ReadingListRemoteCatalogService:
    return ReadingListRemoteCatalogService(SEED_DIR / "reading_list.example.yaml")


def get_reading_catalog(
    store: Annotated[ReadingListCatalogStore, Depends(get_catalog_store)],
) -> ReadingListCatalogService:
    return load_effective_reading_catalog(seed_path=SEED_DIR / "reading_list.example.yaml", store=store)


@router.get("/sources", response_model=list[ReadingListSource])
def list_reading_sources(
    catalog: Annotated[ReadingListCatalogService, Depends(get_reading_catalog)],
) -> list[ReadingListSource]:
    return catalog.catalog.sources


@router.get("/books", response_model=list[ReadingListBook])
def list_reading_books(
    catalog: Annotated[ReadingListCatalogService, Depends(get_reading_catalog)],
    category: str | None = None,
    open_source_only: bool = False,
) -> list[ReadingListBook]:
    return catalog.list_books(category=category, open_source_only=open_source_only)


@router.get("/books/{slug}/summary", response_model=ReadingListBookSummary)
def summarize_reading_book(
    slug: str,
    catalog: Annotated[ReadingListCatalogService, Depends(get_reading_catalog)],
) -> ReadingListBookSummary:
    summary = catalog.summarize_book(slug)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Unknown reading-list book: {slug}")
    return summary


@router.post(
    "/refresh",
    response_model=list[ReadingListBook],
    dependencies=[LocalApiKeyDependency],
)
def refresh_reading_catalog(
    store: Annotated[ReadingListCatalogStore, Depends(get_catalog_store)],
    service: Annotated[ReadingListRemoteCatalogService, Depends(get_remote_catalog_service)],
) -> list[ReadingListBook]:
    return service.refresh(store).books
