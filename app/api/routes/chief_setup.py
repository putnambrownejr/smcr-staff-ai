from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.chief_setup import ChiefSetup, ChiefSetupResponse, ChiefSetupUpsertRequest
from app.services.chief.setup_store import (
    ChiefSetupStore,
    build_chief_briefing_block,
    is_configured,
)

router = APIRouter(prefix="/chief-setup", tags=["chief setup"], dependencies=[LocalApiKeyDependency])


def get_chief_setup_store() -> Iterator[ChiefSetupStore]:
    settings = get_settings()
    yield ChiefSetupStore(settings.chief_setup_storage_dir)


def _response(setup: ChiefSetup) -> ChiefSetupResponse:
    return ChiefSetupResponse(
        setup=setup,
        briefing_block=build_chief_briefing_block(setup),
        is_configured=is_configured(setup),
    )


@router.get("/{user_key}", response_model=ChiefSetupResponse)
def get_chief_setup(
    user_key: str,
    store: Annotated[ChiefSetupStore, Depends(get_chief_setup_store)],
) -> ChiefSetupResponse:
    setup = store.get(user_key) or ChiefSetup(user_key=user_key)
    return _response(setup)


@router.put("/{user_key}", response_model=ChiefSetupResponse)
def upsert_chief_setup(
    user_key: str,
    body: ChiefSetupUpsertRequest,
    store: Annotated[ChiefSetupStore, Depends(get_chief_setup_store)],
) -> ChiefSetupResponse:
    try:
        setup = store.upsert(user_key, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _response(setup)


@router.delete("/{user_key}", status_code=204)
def delete_chief_setup(
    user_key: str,
    store: Annotated[ChiefSetupStore, Depends(get_chief_setup_store)],
) -> None:
    if not store.delete(user_key):
        raise HTTPException(status_code=404, detail="No Chief of Staff setup for this user.")
