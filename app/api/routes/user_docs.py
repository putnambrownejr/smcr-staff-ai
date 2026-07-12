from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.user_docs import (
    SaveToProjectRequest,
    SaveToProjectResponse,
    UserDocCategory,
    UserDocCreateRequest,
    UserDocEntry,
    UserDocUpdateRequest,
)
from app.services.user_docs.store import UserDocsStore

router = APIRouter(prefix="/user-docs", tags=["user docs"], dependencies=[LocalApiKeyDependency])


def get_user_docs_store() -> Iterator[UserDocsStore]:
    settings = get_settings()
    yield UserDocsStore(settings.user_docs_dir, settings.projects_dir)


@router.get("/projects", response_model=list[str])
def list_projects(store: Annotated[UserDocsStore, Depends(get_user_docs_store)]) -> list[str]:
    return store.list_projects()


@router.get("/{category}/{user_key}", response_model=list[UserDocEntry])
def list_user_docs(
    category: UserDocCategory,
    user_key: str,
    store: Annotated[UserDocsStore, Depends(get_user_docs_store)],
) -> list[UserDocEntry]:
    return store.list_category(category, user_key)


@router.post("/{category}/{user_key}", response_model=UserDocEntry, status_code=201)
def create_user_doc(
    category: UserDocCategory,
    user_key: str,
    body: UserDocCreateRequest,
    store: Annotated[UserDocsStore, Depends(get_user_docs_store)],
) -> UserDocEntry:
    try:
        return store.create(category, user_key, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{category}/{user_key}/{doc_id}", response_model=UserDocEntry)
def get_user_doc(
    category: UserDocCategory,
    user_key: str,
    doc_id: str,
    store: Annotated[UserDocsStore, Depends(get_user_docs_store)],
) -> UserDocEntry:
    entry = store.get(category, user_key, doc_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Unknown user doc: {doc_id}")
    return entry


@router.patch("/{category}/{user_key}/{doc_id}", response_model=UserDocEntry)
def update_user_doc(
    category: UserDocCategory,
    user_key: str,
    doc_id: str,
    body: UserDocUpdateRequest,
    store: Annotated[UserDocsStore, Depends(get_user_docs_store)],
) -> UserDocEntry:
    entry = store.update(category, user_key, doc_id, body)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Unknown user doc: {doc_id}")
    return entry


@router.delete("/{category}/{user_key}/{doc_id}", status_code=204)
def delete_user_doc(
    category: UserDocCategory,
    user_key: str,
    doc_id: str,
    store: Annotated[UserDocsStore, Depends(get_user_docs_store)],
) -> None:
    if not store.delete(category, user_key, doc_id):
        raise HTTPException(status_code=404, detail=f"Unknown user doc: {doc_id}")


@router.post("/{category}/{user_key}/{doc_id}/save-to-project", response_model=SaveToProjectResponse)
def save_user_doc_to_project(
    category: UserDocCategory,
    user_key: str,
    doc_id: str,
    body: SaveToProjectRequest,
    store: Annotated[UserDocsStore, Depends(get_user_docs_store)],
) -> SaveToProjectResponse:
    try:
        path = store.save_to_project(category, user_key, doc_id, body.project)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SaveToProjectResponse(path=path.as_posix(), message=f"Saved to {body.project}.")
