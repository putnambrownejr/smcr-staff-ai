from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.reading_state import (
    ReadingProgressListResponse,
    ReadingProgressRecord,
    UpsertReadingProgressRequest,
)
from app.services.reading.catalog import ReadingListCatalogService
from app.services.reading.catalog_store import ReadingListCatalogStore
from app.services.reading.live_catalog import load_effective_reading_catalog
from app.services.reading.state_store import ReadingProgressStore

router = APIRouter(
    prefix="/reading-list",
    tags=["professional reading state"],
    dependencies=[LocalApiKeyDependency],
)

SEED_DIR = Path(__file__).resolve().parents[3] / "data" / "seed"


def get_reading_state_store() -> Iterator[ReadingProgressStore]:
    yield ReadingProgressStore(get_settings().reading_state_storage_dir)


def get_reading_catalog() -> ReadingListCatalogService:
    settings = get_settings()
    return load_effective_reading_catalog(
        seed_path=SEED_DIR / "reading_list.example.yaml",
        store=ReadingListCatalogStore(settings.reading_catalog_storage_dir),
    )


@router.get("/state/{user_key}", response_model=ReadingProgressListResponse)
def list_reading_progress(
    user_key: str,
    store: Annotated[ReadingProgressStore, Depends(get_reading_state_store)],
) -> ReadingProgressListResponse:
    return store.list(user_key)


@router.put("/state/{user_key}/{slug}", response_model=ReadingProgressRecord)
def upsert_reading_progress(
    user_key: str,
    slug: str,
    request: UpsertReadingProgressRequest,
    store: Annotated[ReadingProgressStore, Depends(get_reading_state_store)],
    catalog: Annotated[ReadingListCatalogService, Depends(get_reading_catalog)],
) -> ReadingProgressRecord:
    book = catalog.get_book(slug)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Unknown reading-list book: {slug}")
    return store.upsert(user_key, book, request)
