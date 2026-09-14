from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.handoff_updates import (
    HandoffApplyUpdateRequest,
    HandoffApplyUpdateResponse,
    HandoffDraftUpdateResponse,
    HandoffUpdateDraftRequest,
)
from app.schemas.session import DrillHandoffJournalRequest, HandoffUpsertResponse, UserSessionHandoff
from app.services.session.handoff_store import SessionHandoffStore
from app.services.session.handoff_updater import HandoffUpdater

router = APIRouter(prefix="/handoffs", tags=["session handoffs"], dependencies=[LocalApiKeyDependency])


def get_handoff_store() -> Iterator[SessionHandoffStore]:
    yield SessionHandoffStore(get_settings().session_handoff_storage_dir)


def get_handoff_updater(
    store: Annotated[SessionHandoffStore, Depends(get_handoff_store)],
) -> HandoffUpdater:
    return HandoffUpdater(store)


@router.put("/{user_key}", response_model=HandoffUpsertResponse)
def upsert_handoff(
    user_key: str,
    handoff: UserSessionHandoff,
    store: Annotated[SessionHandoffStore, Depends(get_handoff_store)],
) -> HandoffUpsertResponse:
    if handoff.user_key != user_key:
        raise HTTPException(status_code=400, detail="Path user_key must match handoff.user_key.")
    # Older clients do not know about the journal. Keep it when their profile
    # update omits the field; an explicit [] still clears it intentionally.
    if "drill_handoffs" not in handoff.model_fields_set:
        existing = store.get(user_key)
        if existing is not None:
            handoff.drill_handoffs = existing.drill_handoffs
            if "admin_watch_items" not in handoff.model_fields_set:
                handoff.admin_watch_items = existing.admin_watch_items
            if "recurring_drill_notes" not in handoff.model_fields_set:
                handoff.recurring_drill_notes = existing.recurring_drill_notes
    try:
        saved = store.upsert(handoff)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return HandoffUpsertResponse(
        handoff=saved,
        message="Saved local session handoff. Keep minimum necessary user context only.",
    )


@router.get("/{user_key}", response_model=UserSessionHandoff)
def get_handoff(
    user_key: str,
    store: Annotated[SessionHandoffStore, Depends(get_handoff_store)],
) -> UserSessionHandoff:
    handoff = store.get(user_key)
    if handoff is None:
        raise HTTPException(status_code=404, detail=f"Unknown handoff: {user_key}")
    return handoff


@router.patch("/{user_key}/journal", response_model=UserSessionHandoff)
def save_drill_journal(
    user_key: str,
    request: DrillHandoffJournalRequest,
    store: Annotated[SessionHandoffStore, Depends(get_handoff_store)],
) -> UserSessionHandoff:
    if len({entry.id for entry in request.entries}) != len(request.entries):
        raise HTTPException(status_code=422, detail="Handoff IDs must be unique.")
    handoff = store.get(user_key) or UserSessionHandoff(user_key=user_key)
    handoff.drill_handoffs = request.entries
    handoff.updated_at = datetime.now(UTC)
    latest = next((entry for entry in request.entries if not entry.archived), None)
    handoff.admin_watch_items = [line.strip() for line in latest.admin.splitlines() if line.strip()] if latest else []
    handoff.recurring_drill_notes = [line.strip() for line in latest.drill.splitlines() if line.strip()] if latest else []
    try:
        return store.upsert(handoff)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{user_key}/draft-update", response_model=HandoffDraftUpdateResponse)
def draft_handoff_update(
    user_key: str,
    request: HandoffUpdateDraftRequest,
    updater: Annotated[HandoffUpdater, Depends(get_handoff_updater)],
) -> HandoffDraftUpdateResponse:
    return updater.draft_update(user_key, request)


@router.post("/{user_key}/apply-update", response_model=HandoffApplyUpdateResponse)
def apply_handoff_update(
    user_key: str,
    request: HandoffApplyUpdateRequest,
    updater: Annotated[HandoffUpdater, Depends(get_handoff_updater)],
) -> HandoffApplyUpdateResponse:
    try:
        return updater.apply_update(user_key, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{user_key}", status_code=204)
def delete_handoff(
    user_key: str,
    store: Annotated[SessionHandoffStore, Depends(get_handoff_store)],
) -> None:
    if not store.delete(user_key):
        raise HTTPException(status_code=404, detail=f"Unknown handoff: {user_key}")
