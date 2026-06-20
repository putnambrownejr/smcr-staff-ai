from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.resource_links import (
    CATEGORY_LABELS,
    ResourceLink,
    ResourceLinkCategory,
    ResourceLinkCreate,
    ResourceLinksResponse,
)
from app.services.staff.resource_links_store import ResourceLinksStore

router = APIRouter(prefix="/resource-links", tags=["resource links"], dependencies=[LocalApiKeyDependency])

_SEED_PATH = Path(__file__).resolve().parents[3] / "data" / "seed" / "resource_links.json"


def get_resource_links_store() -> Iterator[ResourceLinksStore]:
    settings = get_settings()
    yield ResourceLinksStore(settings.resource_links_storage_dir, _SEED_PATH)


@router.get("/{user_key}", response_model=ResourceLinksResponse)
def list_resource_links(
    user_key: str,
    store: Annotated[ResourceLinksStore, Depends(get_resource_links_store)],
    category: Annotated[ResourceLinkCategory | None, Query()] = None,
) -> ResourceLinksResponse:
    links = store.get_all(user_key, category=category)
    return ResourceLinksResponse(
        links=links,
        total=len(links),
        categories={c.value: label for c, label in CATEGORY_LABELS.items()},
    )


@router.post("/{user_key}", response_model=ResourceLink, status_code=201)
def add_resource_link(
    user_key: str,
    body: ResourceLinkCreate,
    store: Annotated[ResourceLinksStore, Depends(get_resource_links_store)],
) -> ResourceLink:
    try:
        return store.add(user_key, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{user_key}/{link_id}", status_code=204)
def delete_resource_link(
    user_key: str,
    link_id: str,
    store: Annotated[ResourceLinksStore, Depends(get_resource_links_store)],
) -> None:
    if not store.delete(user_key, link_id):
        raise HTTPException(status_code=404, detail=f"Link '{link_id}' not found in user store.")
