from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.sharing import ExternalAiPacketRequest, ExternalAiPacketResponse
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.opportunities.tracker import OpportunityTracker
from app.services.session.active_context_store import ActiveUserContextStore
from app.services.session.handoff_store import SessionHandoffStore
from app.services.sharing.external_ai_packet import ExternalAiPacketBuilder
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/sharing", tags=["external ai sharing"], dependencies=[LocalApiKeyDependency])


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_handoff_store() -> Iterator[SessionHandoffStore]:
    yield SessionHandoffStore(get_settings().session_handoff_storage_dir)


def get_active_context_store() -> Iterator[ActiveUserContextStore]:
    settings = get_settings()
    yield ActiveUserContextStore(f"{settings.local_context_storage_dir}/active_user_context")


def get_plan_store() -> Iterator[DrillPrepPlanStore]:
    yield DrillPrepPlanStore(f"{get_settings().local_context_storage_dir}/drill_plans")


def get_opportunity_tracker() -> Iterator[OpportunityTracker]:
    yield OpportunityTracker(f"{get_settings().local_context_storage_dir}/opportunities")


def get_document_organizer(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> PersonalDocumentOrganizer:
    return PersonalDocumentOrganizer(store)


@router.post("/external-ai-packet", response_model=ExternalAiPacketResponse)
def build_external_ai_packet(
    request: ExternalAiPacketRequest,
    handoff_store: Annotated[SessionHandoffStore, Depends(get_handoff_store)],
    active_context_store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
    plan_store: Annotated[DrillPrepPlanStore, Depends(get_plan_store)],
    opportunity_tracker: Annotated[OpportunityTracker, Depends(get_opportunity_tracker)],
    document_organizer: Annotated[PersonalDocumentOrganizer, Depends(get_document_organizer)],
) -> ExternalAiPacketResponse:
    builder = ExternalAiPacketBuilder()
    return builder.build(
        request,
        handoff=handoff_store.get(request.user_key),
        active_user_context=active_context_store.get(request.user_key),
        document_summary=document_organizer.list_documents() if request.include_document_summary else None,
        drill_plans=plan_store.list() if request.include_drill_plans else None,
        opportunities=list(opportunity_tracker.list()) if request.include_opportunities else None,
    )
