from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.personal_documents import PersonalDocumentSummary
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(
    prefix="/personal-documents",
    tags=["personal documents"],
    dependencies=[LocalApiKeyDependency],
)


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_document_organizer(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> PersonalDocumentOrganizer:
    return PersonalDocumentOrganizer(store)


@router.get("", response_model=PersonalDocumentSummary)
def list_personal_documents(
    organizer: Annotated[PersonalDocumentOrganizer, Depends(get_document_organizer)],
    document_type: str | None = None,
) -> PersonalDocumentSummary:
    return organizer.list_documents(document_type=document_type)
