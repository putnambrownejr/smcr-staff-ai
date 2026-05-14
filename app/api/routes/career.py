from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.career import CareerWatchResponse
from app.services.career.watch import CareerWatchService
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/career", tags=["career watch"], dependencies=[LocalApiKeyDependency])
SEED_DIR = Path("data/seed")


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_career_watch_service(
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> CareerWatchService:
    settings = get_settings()
    return CareerWatchService(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(context_store),
        opportunity_tracker=OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities"),
        reading_catalog=ReadingListCatalogService.from_yaml(SEED_DIR / "reading_list.example.yaml"),
    )


@router.get("/watch/{user_key}", response_model=CareerWatchResponse)
def get_career_watch(
    user_key: str,
    service: Annotated[CareerWatchService, Depends(get_career_watch_service)],
) -> CareerWatchResponse:
    return service.build_watch(user_key)
