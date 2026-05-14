from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.actions import (
    ActionRecord,
    ActionStatus,
    ActionTrackRequest,
    ActionTrackResponse,
    ActionUpdateRequest,
)
from app.services.actions.tracker import ActionTracker

router = APIRouter(prefix="/actions", tags=["action tracker"], dependencies=[LocalApiKeyDependency])


def get_tracker() -> Iterator[ActionTracker]:
    settings = get_settings()
    yield ActionTracker(f"{settings.local_context_storage_dir}/actions")


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


@router.delete("/{action_id}", status_code=204)
def delete_action(
    action_id: str,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> None:
    if not tracker.delete(action_id):
        raise HTTPException(status_code=404, detail=f"Unknown action item: {action_id}")
