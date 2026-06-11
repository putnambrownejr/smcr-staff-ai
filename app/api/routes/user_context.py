from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.user_context import ActiveUserContext, ActiveUserContextUpsertResponse
from app.services.session.active_context_store import ActiveUserContextStore

router = APIRouter(prefix="/user-context", tags=["active user context"], dependencies=[LocalApiKeyDependency])


def get_active_context_store() -> Iterator[ActiveUserContextStore]:
    settings = get_settings()
    yield ActiveUserContextStore(settings.active_user_context_storage_dir)


@router.put("/{user_key}", response_model=ActiveUserContextUpsertResponse)
def upsert_active_user_context(
    user_key: str,
    context: ActiveUserContext,
    store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
) -> ActiveUserContextUpsertResponse:
    if context.user_key != user_key:
        raise HTTPException(status_code=400, detail="Path user_key must match active_user_context.user_key.")
    saved = store.upsert(context)
    return ActiveUserContextUpsertResponse(
        active_user_context=saved,
        message="Saved local active user context for temporary staff-bias and unit-shaping use.",
    )


@router.get("/{user_key}", response_model=ActiveUserContext)
def get_active_user_context(
    user_key: str,
    store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
) -> ActiveUserContext:
    context = store.get(user_key)
    if context is None:
        raise HTTPException(status_code=404, detail=f"Unknown or expired active user context: {user_key}")
    return context


@router.delete("/{user_key}", status_code=204)
def delete_active_user_context(
    user_key: str,
    store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
) -> None:
    if not store.delete(user_key):
        raise HTTPException(status_code=404, detail=f"Unknown active user context: {user_key}")
