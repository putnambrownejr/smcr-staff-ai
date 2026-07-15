from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.chief import ChiefBriefRequest, ChiefBriefResponse
from app.schemas.chief_capabilities import (
    ChiefCapabilityRequest,
    ChiefCapabilityResponse,
    ChiefDomainSummary,
    ChiefUndoRequest,
    ChiefUndoResponse,
)
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.chief.capability_audit_store import CapabilityAuditStore
from app.services.chief.capability_gateway import ChiefCapabilityGateway
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.fitness.cadence_store import CadenceStore
from app.services.fitreps.store import FitrepStore
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog_store import ReadingListCatalogStore
from app.services.reading.live_catalog import load_effective_reading_catalog
from app.services.session.active_context_store import ActiveUserContextStore
from app.services.session.handoff_store import SessionHandoffStore
from app.services.staff.battle_rhythm_store import BattleRhythmStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/chief", tags=["chief aide"], dependencies=[LocalApiKeyDependency])
REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = REPO_ROOT / "data" / "seed"


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_capability_gateway() -> ChiefCapabilityGateway:
    settings = get_settings()
    return ChiefCapabilityGateway(
        travel_store=TravelCaseStore(settings.travel_case_storage_dir),
        fitrep_store=FitrepStore(settings.fitrep_storage_dir),
        cadence_store=CadenceStore(settings.cadence_storage_dir),
        audit_store=CapabilityAuditStore(settings.chief_capability_audit_storage_dir),
        repository_root=REPO_ROOT,
    )


def get_orchestrator(
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
    capability_gateway: Annotated[ChiefCapabilityGateway, Depends(get_capability_gateway)],
) -> ChiefAideOrchestrator:
    settings = get_settings()
    return ChiefAideOrchestrator(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(context_store),
        drill_plan_store=DrillPrepPlanStore(settings.drill_plans_storage_dir),
        reading_catalog=load_effective_reading_catalog(
            seed_path=SEED_DIR / "reading_list.example.yaml",
            store=ReadingListCatalogStore(settings.reading_catalog_storage_dir),
        ),
        document_update_store=DocumentUpdateStore(settings.document_updates_storage_dir),
        opportunity_tracker=OpportunityTracker(settings.opportunities_storage_dir),
        active_context_store=ActiveUserContextStore(settings.active_user_context_storage_dir),
        travel_case_store=TravelCaseStore(settings.travel_case_storage_dir),
        battle_rhythm_store=BattleRhythmStore(settings.battle_rhythm_storage_dir),
        capability_gateway=capability_gateway,
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


@router.post("/capabilities", response_model=ChiefCapabilityResponse)
def execute_chief_capability(
    request: ChiefCapabilityRequest,
    gateway: Annotated[ChiefCapabilityGateway, Depends(get_capability_gateway)],
) -> ChiefCapabilityResponse:
    try:
        return gateway.execute(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capabilities/undo", response_model=ChiefUndoResponse)
def undo_chief_capability(
    request: ChiefUndoRequest,
    gateway: Annotated[ChiefCapabilityGateway, Depends(get_capability_gateway)],
) -> ChiefUndoResponse:
    try:
        return gateway.undo(request.user_key, request.undo_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/capabilities/{user_key}/summary", response_model=ChiefDomainSummary)
def get_chief_capability_summary(
    user_key: str,
    gateway: Annotated[ChiefCapabilityGateway, Depends(get_capability_gateway)],
) -> ChiefDomainSummary:
    return gateway.summary(user_key)
