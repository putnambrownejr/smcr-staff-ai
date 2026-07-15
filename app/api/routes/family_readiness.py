from collections.abc import Callable, Iterator
from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.family_readiness import (
    FamilyReadinessContactUpsertRequest,
    FamilyReadinessEvent,
    FamilyReadinessEventCreateRequest,
    FamilyReadinessEventListResponse,
    FamilyReadinessEventUpdateRequest,
    FamilyReadinessGlossaryUpsertRequest,
    FamilyReadinessItemCreateRequest,
    FamilyReadinessItemOrderRequest,
    FamilyReadinessItemUpdateRequest,
    FamilyReadinessMilestoneUpdateRequest,
    FamilyReadinessSummaryRequest,
)
from app.schemas.user_docs import UserDocCategory, UserDocCreateRequest, UserDocEntry
from app.services.family_readiness.builder import render_spouse_summary
from app.services.family_readiness.calendar import FamilyReadinessIcsProvider
from app.services.family_readiness.store import FamilyReadinessStore
from app.services.user_docs.store import UserDocsStore

router = APIRouter(
    prefix="/family-readiness",
    tags=["family readiness"],
    dependencies=[LocalApiKeyDependency],
)
_ics = FamilyReadinessIcsProvider()


def get_family_readiness_store() -> Iterator[FamilyReadinessStore]:
    yield FamilyReadinessStore(get_settings().family_readiness_storage_dir)


def get_family_readiness_user_docs_store() -> Iterator[UserDocsStore]:
    settings = get_settings()
    yield UserDocsStore(settings.user_docs_dir, settings.projects_dir)


@router.get("/{user_key}", response_model=FamilyReadinessEventListResponse)
def list_events(
    user_key: str,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEventListResponse:
    records = store.list(user_key)
    return FamilyReadinessEventListResponse(total_events=len(records), records=records)


@router.post("/{user_key}", response_model=FamilyReadinessEvent, status_code=201)
def create_event(
    user_key: str,
    request: FamilyReadinessEventCreateRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    _matching_user_key(user_key, request.user_key)
    try:
        return store.create(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{user_key}/{event_id}", response_model=FamilyReadinessEvent)
def get_event(
    user_key: str,
    event_id: str,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    event = store.get(user_key, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Unknown family readiness event: {event_id}")
    return event


@router.patch("/{user_key}/{event_id}", response_model=FamilyReadinessEvent)
def update_event(
    user_key: str,
    event_id: str,
    request: FamilyReadinessEventUpdateRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    return _store_call(lambda: store.update_event(user_key, event_id, request))


@router.post("/{user_key}/{event_id}/items", response_model=FamilyReadinessEvent)
def add_item(
    user_key: str,
    event_id: str,
    request: FamilyReadinessItemCreateRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    return _store_call(lambda: store.add_item(user_key, event_id, request))


@router.patch("/{user_key}/{event_id}/items/{item_id}", response_model=FamilyReadinessEvent)
def update_item(
    user_key: str,
    event_id: str,
    item_id: str,
    request: FamilyReadinessItemUpdateRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    return _store_call(lambda: store.update_item(user_key, event_id, item_id, request))


@router.put("/{user_key}/{event_id}/item-order", response_model=FamilyReadinessEvent)
def reorder_items(
    user_key: str,
    event_id: str,
    request: FamilyReadinessItemOrderRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    return _store_call(lambda: store.reorder_items(user_key, event_id, request))


@router.post("/{user_key}/{event_id}/contacts", response_model=FamilyReadinessEvent)
def upsert_contact(
    user_key: str,
    event_id: str,
    request: FamilyReadinessContactUpsertRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    return _store_call(lambda: store.upsert_contact(user_key, event_id, request))


@router.delete("/{user_key}/{event_id}/contacts/{contact_id}", response_model=FamilyReadinessEvent)
def delete_contact(
    user_key: str,
    event_id: str,
    contact_id: str,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    return _store_call(lambda: store.delete_contact(user_key, event_id, contact_id))


@router.put("/{user_key}/{event_id}/glossary/{term}", response_model=FamilyReadinessEvent)
def upsert_glossary(
    user_key: str,
    event_id: str,
    term: str,
    request: FamilyReadinessGlossaryUpsertRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    if unquote(term).casefold() != request.term.casefold():
        raise HTTPException(status_code=400, detail="Glossary term in path and body must match.")
    return _store_call(lambda: store.upsert_glossary(user_key, event_id, request))


@router.delete("/{user_key}/{event_id}/glossary/{term}", response_model=FamilyReadinessEvent)
def delete_glossary(
    user_key: str,
    event_id: str,
    term: str,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    return _store_call(lambda: store.delete_glossary(user_key, event_id, unquote(term)))


@router.patch("/{user_key}/{event_id}/milestones/{milestone_id}", response_model=FamilyReadinessEvent)
def update_milestone(
    user_key: str,
    event_id: str,
    milestone_id: str,
    request: FamilyReadinessMilestoneUpdateRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> FamilyReadinessEvent:
    return _store_call(lambda: store.update_milestone(user_key, event_id, milestone_id, request))


@router.get("/{user_key}/{event_id}/ics")
def export_ics(
    user_key: str,
    event_id: str,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> Response:
    event = get_event(user_key, event_id, store)
    return Response(
        content=_ics.export(event),
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="family-readiness-{event_id}.ics"'},
    )


@router.post("/{user_key}/{event_id}/summary", response_model=UserDocEntry, status_code=201)
def create_summary(
    user_key: str,
    event_id: str,
    request: FamilyReadinessSummaryRequest,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
    user_docs: Annotated[UserDocsStore, Depends(get_family_readiness_user_docs_store)],
) -> UserDocEntry:
    _matching_user_key(user_key, request.user_key)
    event = get_event(user_key, event_id, store)
    return user_docs.create(
        UserDocCategory.generations,
        user_key,
        UserDocCreateRequest(
            title=f"{event.title} — Family readiness summary",
            body=render_spouse_summary(event),
            fields={
                "templateType": "family_readiness_summary",
                "familyReadinessEventId": event.event_id,
            },
        ),
    )


@router.delete("/{user_key}/{event_id}", status_code=204)
def delete_event(
    user_key: str,
    event_id: str,
    store: Annotated[FamilyReadinessStore, Depends(get_family_readiness_store)],
) -> None:
    if not store.delete(user_key, event_id):
        raise HTTPException(status_code=404, detail=f"Unknown family readiness event: {event_id}")


def _matching_user_key(path_user_key: str, body_user_key: str) -> None:
    if path_user_key != body_user_key:
        raise HTTPException(status_code=400, detail="user_key in path and body must match.")


def _store_call(operation: Callable[[], FamilyReadinessEvent]) -> FamilyReadinessEvent:
    try:
        return operation()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
