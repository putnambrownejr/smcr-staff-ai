from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.context import LocalContextListResponse, LocalContextReadResponse, LocalContextUploadResponse
from app.services.storage.local_context_store import LocalContextStore, parse_tags

router = APIRouter(prefix="/context", tags=["local context"], dependencies=[LocalApiKeyDependency])


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


@router.post("/upload", response_model=LocalContextUploadResponse)
async def upload_context(
    file: Annotated[UploadFile, File()],
    store: Annotated[LocalContextStore, Depends(get_context_store)],
    tags: Annotated[str | None, Form()] = None,
    document_type: Annotated[str, Form()] = "other",
    consent_ack: Annotated[bool, Form()] = False,
    review_date: Annotated[date | None, Form()] = None,
    expiration_date: Annotated[date | None, Form()] = None,
) -> LocalContextUploadResponse:
    content = await file.read()
    try:
        item = store.save(
            filename=file.filename or "upload.bin",
            content=content,
            content_type=file.content_type or "application/octet-stream",
            tags=parse_tags(tags),
            document_type=document_type,
            consent_ack=consent_ack,
            review_date=review_date,
            expiration_date=expiration_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return LocalContextUploadResponse(
        item=item,
        message=(
            "Stored as local advisory context only. This upload does not modify doctrine, org hierarchy, "
            "exercise cadence, agent registry, or canonical document structure."
        ),
    )


@router.get("", response_model=LocalContextListResponse)
def list_context(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> LocalContextListResponse:
    return LocalContextListResponse(items=store.list())


@router.get("/{context_id}", response_model=LocalContextReadResponse)
def read_context(
    context_id: str,
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> LocalContextReadResponse:
    item = store.get(context_id)
    preview = store.read_preview(context_id)
    if item is None or preview is None:
        raise HTTPException(status_code=404, detail=f"Unknown local context item: {context_id}")
    return LocalContextReadResponse(item=item, text_preview=preview)


@router.delete("/{context_id}", status_code=204)
def delete_context(
    context_id: str,
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> None:
    if not store.delete(context_id):
        raise HTTPException(status_code=404, detail=f"Unknown local context item: {context_id}")
