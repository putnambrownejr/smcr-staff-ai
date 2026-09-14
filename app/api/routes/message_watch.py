from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.ingestion import MessageRecord
from app.schemas.message_watch import MessageWatchRefreshResponse
from app.services.ingestion.almar_feed_service import AlmarFeedService
from app.services.ingestion.dod_watch_service import DodWatchService
from app.services.ingestion.message_record_store import MessageRecordStore

router = APIRouter(prefix="/message-watch", tags=["message watch"], dependencies=[LocalApiKeyDependency])


def get_almar_store() -> Iterator[MessageRecordStore]:
    settings = get_settings()
    yield MessageRecordStore(settings.almar_feed_storage_dir)


def get_dod_store() -> Iterator[MessageRecordStore]:
    settings = get_settings()
    yield MessageRecordStore(settings.dod_watch_storage_dir)


def get_almar_service() -> AlmarFeedService:
    return AlmarFeedService()


def get_dod_service() -> DodWatchService:
    return DodWatchService()


@router.get("/almars/feed", response_model=list[MessageRecord])
def list_almars(
    store: Annotated[MessageRecordStore, Depends(get_almar_store)],
    limit: int = 25,
) -> list[MessageRecord]:
    return store.list(limit=limit)


@router.post("/almars/refresh", response_model=MessageWatchRefreshResponse)
def refresh_almars(
    store: Annotated[MessageRecordStore, Depends(get_almar_store)],
    service: Annotated[AlmarFeedService, Depends(get_almar_service)],
) -> MessageWatchRefreshResponse:
    return service.refresh(store)


@router.get("/dod/feed", response_model=list[MessageRecord])
def list_dod_watch(
    store: Annotated[MessageRecordStore, Depends(get_dod_store)],
    limit: int = 25,
) -> list[MessageRecord]:
    return store.list(limit=limit)


@router.post("/dod/refresh", response_model=MessageWatchRefreshResponse)
def refresh_dod_watch(
    store: Annotated[MessageRecordStore, Depends(get_dod_store)],
    service: Annotated[DodWatchService, Depends(get_dod_service)],
) -> MessageWatchRefreshResponse:
    return service.refresh(store)
