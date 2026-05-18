from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.ingestion import MessageRecord
from app.schemas.message_watch import MessageWatchRefreshResponse
from app.services.ingestion.dod_watch_service import DodWatchService
from app.services.ingestion.message_record_store import MessageRecordStore
from app.services.ingestion.navy_message_service import NavyMessageService

router = APIRouter(prefix="/message-watch", tags=["message watch"], dependencies=[LocalApiKeyDependency])


def get_navadmin_store() -> Iterator[MessageRecordStore]:
    settings = get_settings()
    yield MessageRecordStore(Path(settings.navy_message_storage_dir) / "navadmins")


def get_alnav_store() -> Iterator[MessageRecordStore]:
    settings = get_settings()
    yield MessageRecordStore(Path(settings.navy_message_storage_dir) / "alnavs")


def get_dod_store() -> Iterator[MessageRecordStore]:
    settings = get_settings()
    yield MessageRecordStore(settings.dod_watch_storage_dir)


def get_navy_service() -> NavyMessageService:
    return NavyMessageService()


def get_dod_service() -> DodWatchService:
    return DodWatchService()


@router.get("/navadmins/feed", response_model=list[MessageRecord])
def list_navadmins(
    store: Annotated[MessageRecordStore, Depends(get_navadmin_store)],
    limit: int = 25,
) -> list[MessageRecord]:
    return store.list(limit=limit)


@router.post("/navadmins/refresh", response_model=MessageWatchRefreshResponse)
def refresh_navadmins(
    store: Annotated[MessageRecordStore, Depends(get_navadmin_store)],
    service: Annotated[NavyMessageService, Depends(get_navy_service)],
) -> MessageWatchRefreshResponse:
    return service.refresh_navadmins(store)


@router.get("/alnavs/feed", response_model=list[MessageRecord])
def list_alnavs(
    store: Annotated[MessageRecordStore, Depends(get_alnav_store)],
    limit: int = 25,
) -> list[MessageRecord]:
    return store.list(limit=limit)


@router.post("/alnavs/refresh", response_model=MessageWatchRefreshResponse)
def refresh_alnavs(
    store: Annotated[MessageRecordStore, Depends(get_alnav_store)],
    service: Annotated[NavyMessageService, Depends(get_navy_service)],
) -> MessageWatchRefreshResponse:
    return service.refresh_alnavs(store)


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
