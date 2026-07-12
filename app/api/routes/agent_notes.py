from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.agent_notes import AgentNotesResponse, AgentNoteUpdateRequest
from app.services.agents.notes_store import AgentNotesStore

router = APIRouter(prefix="/agent-notes", tags=["agent notes"], dependencies=[LocalApiKeyDependency])


def get_agent_notes_store() -> Iterator[AgentNotesStore]:
    settings = get_settings()
    yield AgentNotesStore(settings.agent_notes_storage_dir)


@router.get("/{user_key}", response_model=AgentNotesResponse)
def get_agent_notes(
    user_key: str,
    store: Annotated[AgentNotesStore, Depends(get_agent_notes_store)],
) -> AgentNotesResponse:
    return store.get(user_key)


@router.put("/{user_key}/agent/{agent_id}", response_model=AgentNotesResponse)
def set_agent_note(
    user_key: str,
    agent_id: str,
    body: AgentNoteUpdateRequest,
    store: Annotated[AgentNotesStore, Depends(get_agent_notes_store)],
) -> AgentNotesResponse:
    try:
        return store.set_note(user_key, "agent", agent_id, body.note)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/{user_key}/skill/{skill_id}", response_model=AgentNotesResponse)
def set_skill_note(
    user_key: str,
    skill_id: str,
    body: AgentNoteUpdateRequest,
    store: Annotated[AgentNotesStore, Depends(get_agent_notes_store)],
) -> AgentNotesResponse:
    try:
        return store.set_note(user_key, "skill", skill_id, body.note)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
