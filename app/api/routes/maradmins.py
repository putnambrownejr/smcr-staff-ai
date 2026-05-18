from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.ingestion import MessageRecord
from app.services.ingestion.maradmin_feed_service import MaradminFeedService
from app.services.ingestion.maradmin_feed_store import MaradminFeedStore

router = APIRouter(prefix="/maradmins", tags=["maradmin feed"], dependencies=[LocalApiKeyDependency])


def get_feed_store() -> Iterator[MaradminFeedStore]:
    yield MaradminFeedStore(get_settings().maradmin_feed_storage_dir)


def get_feed_service() -> MaradminFeedService:
    return MaradminFeedService()


@router.get("/feed", response_model=list[MessageRecord])
def list_maradmin_feed(
    store: Annotated[MaradminFeedStore, Depends(get_feed_store)],
    limit: int = 10,
) -> list[MessageRecord]:
    return store.list(limit=limit)


@router.post("/refresh", response_model=list[MessageRecord])
def refresh_maradmin_feed(
    store: Annotated[MaradminFeedStore, Depends(get_feed_store)],
    service: Annotated[MaradminFeedService, Depends(get_feed_service)],
) -> list[MessageRecord]:
    return service.refresh(store)
