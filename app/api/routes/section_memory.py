from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.section_memory import (
    SectionMemoryProfile,
    SectionMemoryProfileUpsertRequest,
    SectionMemoryUpsertResponse,
)
from app.services.staff.section_memory_store import SectionMemoryStore

router = APIRouter(prefix="/section-memory", tags=["section memory"], dependencies=[LocalApiKeyDependency])


def get_section_memory_store() -> Iterator[SectionMemoryStore]:
    settings = get_settings()
    yield SectionMemoryStore(settings.section_memory_storage_dir)


@router.get("/{user_key}", response_model=SectionMemoryProfile)
def get_section_memory_profile(
    user_key: str,
    store: Annotated[SectionMemoryStore, Depends(get_section_memory_store)],
) -> SectionMemoryProfile:
    profile = store.get(user_key)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No section-memory profile stored for {user_key}.")
    return profile


@router.put("/{user_key}", response_model=SectionMemoryUpsertResponse)
def upsert_section_memory_profile(
    user_key: str,
    request: SectionMemoryProfileUpsertRequest,
    store: Annotated[SectionMemoryStore, Depends(get_section_memory_store)],
) -> SectionMemoryUpsertResponse:
    try:
        profile = store.upsert(user_key, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SectionMemoryUpsertResponse(
        profile=profile,
        message="Saved local section-memory profile for recurring staff pain points, checks, and questions.",
    )


@router.delete("/{user_key}", status_code=204)
def delete_section_memory_profile(
    user_key: str,
    store: Annotated[SectionMemoryStore, Depends(get_section_memory_store)],
) -> None:
    if not store.delete(user_key):
        raise HTTPException(status_code=404, detail=f"No section-memory profile stored for {user_key}.")
