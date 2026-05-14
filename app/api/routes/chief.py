from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.chief import ChiefBriefRequest, ChiefBriefResponse
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/chief", tags=["chief aide"], dependencies=[LocalApiKeyDependency])
SEED_DIR = Path("data/seed")


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_orchestrator(
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> ChiefAideOrchestrator:
    settings = get_settings()
    return ChiefAideOrchestrator(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(context_store),
        drill_plan_store=DrillPrepPlanStore(f"{settings.local_context_storage_dir}/drill_plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(SEED_DIR / "reading_list.example.yaml"),
    )


@router.post("/brief", response_model=ChiefBriefResponse)
def build_chief_brief(
    request: ChiefBriefRequest,
    orchestrator: Annotated[ChiefAideOrchestrator, Depends(get_orchestrator)],
) -> ChiefBriefResponse:
    return orchestrator.build_brief(request)


@router.get("/brief/{user_key}", response_model=ChiefBriefResponse)
def get_chief_brief(
    user_key: str,
    orchestrator: Annotated[ChiefAideOrchestrator, Depends(get_orchestrator)],
) -> ChiefBriefResponse:
    return orchestrator.build_brief(ChiefBriefRequest(user_key=user_key))
