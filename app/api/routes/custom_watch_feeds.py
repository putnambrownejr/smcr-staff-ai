from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.custom_watch_feeds import (
    CreateCustomWatchFeedRequest,
    CustomWatchFeed,
    CustomWatchFeedRefreshResponse,
    UpdateCustomWatchFeedRequest,
)
from app.schemas.ingestion import MessageRecord
from app.services.ingestion.custom_watch_feed_service import CustomWatchFeedService
from app.services.ingestion.custom_watch_feed_store import CustomWatchFeedStore

router = APIRouter(
    prefix="/custom-watch-feeds",
    tags=["custom watch feeds"],
    dependencies=[LocalApiKeyDependency],
)


def get_feed_store() -> Iterator[CustomWatchFeedStore]:
    yield CustomWatchFeedStore(get_settings().custom_watch_feed_storage_dir)


def get_feed_service() -> CustomWatchFeedService:
    return CustomWatchFeedService()


@router.get("", response_model=list[CustomWatchFeed])
def list_custom_watch_feeds(
    store: Annotated[CustomWatchFeedStore, Depends(get_feed_store)],
) -> list[CustomWatchFeed]:
    return store.list()


@router.post("", response_model=CustomWatchFeed)
def create_custom_watch_feed(
    request: CreateCustomWatchFeedRequest,
    store: Annotated[CustomWatchFeedStore, Depends(get_feed_store)],
) -> CustomWatchFeed:
    return store.create(request)


@router.patch("/{feed_id}", response_model=CustomWatchFeed)
def update_custom_watch_feed(
    feed_id: str,
    request: UpdateCustomWatchFeedRequest,
    store: Annotated[CustomWatchFeedStore, Depends(get_feed_store)],
) -> CustomWatchFeed:
    record = store.update(feed_id, request)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown custom watch feed: {feed_id}")
    return record


@router.delete("/{feed_id}", status_code=204)
def delete_custom_watch_feed(
    feed_id: str,
    store: Annotated[CustomWatchFeedStore, Depends(get_feed_store)],
) -> None:
    if not store.delete(feed_id):
        raise HTTPException(status_code=404, detail=f"Unknown custom watch feed: {feed_id}")


@router.post("/{feed_id}/refresh", response_model=CustomWatchFeedRefreshResponse)
def refresh_custom_watch_feed(
    feed_id: str,
    store: Annotated[CustomWatchFeedStore, Depends(get_feed_store)],
    service: Annotated[CustomWatchFeedService, Depends(get_feed_service)],
) -> CustomWatchFeedRefreshResponse:
    feed = store.get(feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail=f"Unknown custom watch feed: {feed_id}")
    return service.refresh(feed=feed, store=store)


@router.get("/{feed_id}/items", response_model=list[MessageRecord])
def list_custom_watch_feed_items(
    feed_id: str,
    store: Annotated[CustomWatchFeedStore, Depends(get_feed_store)],
    service: Annotated[CustomWatchFeedService, Depends(get_feed_service)],
    limit: int = 25,
) -> list[MessageRecord]:
    feed = store.get(feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail=f"Unknown custom watch feed: {feed_id}")
    return service.list_items(feed=feed, store=store, limit=limit)
