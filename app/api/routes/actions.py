from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.actions import (
    ActionLinkRequest,
    ActionRecord,
    ActionStatus,
    ActionTrackRequest,
    ActionTrackResponse,
    ActionUpdateRequest,
)
from app.schemas.context import LocalContextMetadata
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.services.actions.tracker import ActionTracker
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/actions", tags=["action tracker"], dependencies=[LocalApiKeyDependency])


def get_tracker() -> Iterator[ActionTracker]:
    settings = get_settings()
    yield ActionTracker(f"{settings.local_context_storage_dir}/actions")


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_update_store() -> Iterator[DocumentUpdateStore]:
    settings = get_settings()
    yield DocumentUpdateStore(f"{settings.local_context_storage_dir}/document_updates")


@router.get("", response_model=list[ActionRecord])
def list_actions(
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
    user_key: str | None = None,
    status: ActionStatus | None = None,
    include_closed: bool = False,
) -> list[ActionRecord]:
    return tracker.list(user_key=user_key, status=status, include_closed=include_closed)


@router.post("/track", response_model=ActionTrackResponse)
def track_actions(
    request: ActionTrackRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionTrackResponse:
    tracked = tracker.track(request.actions)
    return ActionTrackResponse(tracked=tracked, message="Tracked POAM and action items locally.")


@router.patch("/{action_id}", response_model=ActionRecord)
def update_action(
    action_id: str,
    request: ActionUpdateRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionRecord:
    record = tracker.update(action_id, request)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown action item: {action_id}")
    return record


@router.post("/{action_id}/links", response_model=ActionRecord)
def add_action_link(
    action_id: str,
    request: ActionLinkRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> ActionRecord:
    _validate_link_target(request, context_store, update_store)
    record = tracker.add_link(action_id, request)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown action item: {action_id}")
    return record


@router.delete("/{action_id}/links/{link_id}", response_model=ActionRecord)
def remove_action_link(
    action_id: str,
    link_id: str,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionRecord:
    record = tracker.remove_link(action_id, link_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown action item or link: {action_id}/{link_id}")
    return record


@router.delete("/{action_id}", status_code=204)
def delete_action(
    action_id: str,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> None:
    if not tracker.delete(action_id):
        raise HTTPException(status_code=404, detail=f"Unknown action item: {action_id}")


def _validate_link_target(
    request: ActionLinkRequest,
    context_store: LocalContextStore,
    update_store: DocumentUpdateStore,
) -> LocalContextMetadata | DocumentationUpdateCandidate | None:
    if request.link_type.value == "url":
        if request.url is None:
            raise HTTPException(status_code=422, detail="URL links require a url.")
        return None
    if request.link_type.value == "local_context":
        if request.target_id is None:
            raise HTTPException(status_code=422, detail="Local context links require target_id.")
        item = context_store.get(request.target_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"Unknown local context item: {request.target_id}")
        return item
    if request.target_id is None:
        raise HTTPException(status_code=422, detail="Documentation update links require target_id.")
    candidate = update_store.get(request.target_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Unknown documentation update candidate: {request.target_id}")
    return candidate
