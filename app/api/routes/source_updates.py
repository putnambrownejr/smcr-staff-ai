from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.source_updates import (
    DocumentationUpdateCandidate,
    DocumentationUpdateStatusUpdate,
    UpdateReviewStatus,
)
from app.services.ingestion.document_update_store import DocumentUpdateStore

router = APIRouter(prefix="/source-updates", tags=["source updates"], dependencies=[LocalApiKeyDependency])


def get_update_store() -> Iterator[DocumentUpdateStore]:
    settings = get_settings()
    yield DocumentUpdateStore(settings.document_updates_storage_dir)


@router.get("", response_model=list[DocumentationUpdateCandidate])
def list_source_updates(
    store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
    status: UpdateReviewStatus | None = None,
) -> list[DocumentationUpdateCandidate]:
    return store.list(status=status)


@router.post("/{candidate_id}/review", response_model=DocumentationUpdateCandidate)
def review_source_update(
    candidate_id: str,
    update: DocumentationUpdateStatusUpdate,
    store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> DocumentationUpdateCandidate:
    candidate = store.update_status(candidate_id, update)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Unknown documentation update candidate: {candidate_id}")
    return candidate
