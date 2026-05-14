from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.admin import AdminReadinessResponse
from app.schemas.career import CareerWatchResponse
from app.schemas.chief import ChiefBriefRequest, ChiefBriefResponse
from app.schemas.dashboard import DashboardWorkspaceResponse
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.source_updates import DocumentationUpdateCandidate, UpdateReviewStatus
from app.services.admin.readiness import AdminReadinessService
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.career.watch import CareerWatchService
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.demo.scenarios import DEMO_USER_KEY, build_demo_career_watch, build_demo_chief_brief
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(tags=["dashboard"])
_DASHBOARD_HTML = Path(__file__).resolve().parents[2] / "static" / "dashboard" / "index.html"
SEED_DIR = Path("data/seed")


@router.get("/dashboard", summary="Open the lightweight SMCR Staff AI dashboard")
def get_dashboard() -> FileResponse:
    return FileResponse(_DASHBOARD_HTML)


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_document_organizer(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> PersonalDocumentOrganizer:
    return PersonalDocumentOrganizer(store)


def get_chief_orchestrator(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> ChiefAideOrchestrator:
    settings = get_settings()
    return ChiefAideOrchestrator(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(store),
        drill_plan_store=DrillPrepPlanStore(f"{settings.local_context_storage_dir}/drill_plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(SEED_DIR / "reading_list.example.yaml"),
        document_update_store=DocumentUpdateStore(f"{settings.local_context_storage_dir}/document_updates"),
        opportunity_tracker=OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities"),
    )


def get_admin_service(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> AdminReadinessService:
    settings = get_settings()
    return AdminReadinessService(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(store),
    )


def get_career_service(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> CareerWatchService:
    settings = get_settings()
    return CareerWatchService(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(store),
        opportunity_tracker=OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities"),
        reading_catalog=ReadingListCatalogService.from_yaml(SEED_DIR / "reading_list.example.yaml"),
    )


def get_opportunity_tracker() -> Iterator[OpportunityTracker]:
    settings = get_settings()
    yield OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities")


def get_update_store() -> Iterator[DocumentUpdateStore]:
    settings = get_settings()
    yield DocumentUpdateStore(f"{settings.local_context_storage_dir}/document_updates")


@router.get(
    "/dashboard/data/{user_key}",
    response_model=DashboardWorkspaceResponse,
    dependencies=[LocalApiKeyDependency],
    summary="Load a consolidated personal dashboard workspace payload",
)
def get_dashboard_data(
    user_key: str,
    orchestrator: Annotated[ChiefAideOrchestrator, Depends(get_chief_orchestrator)],
    admin_service: Annotated[AdminReadinessService, Depends(get_admin_service)],
    career_service: Annotated[CareerWatchService, Depends(get_career_service)],
    organizer: Annotated[PersonalDocumentOrganizer, Depends(get_document_organizer)],
    opportunity_tracker: Annotated[OpportunityTracker, Depends(get_opportunity_tracker)],
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> DashboardWorkspaceResponse:
    chief_brief = orchestrator.build_brief(ChiefBriefRequest(user_key=user_key))
    admin_readiness = admin_service.build(user_key)
    career_watch = career_service.build_watch(user_key)
    document_summary = organizer.list_documents()
    tracked_opportunities = list(opportunity_tracker.list())[:8]
    documentation_updates = [
        item for item in update_store.list() if item.review_status != UpdateReviewStatus.ignored
    ][:8]
    return _workspace_response(
        mode="personal",
        user_key=user_key,
        chief_brief=chief_brief,
        admin_readiness=admin_readiness,
        career_watch=career_watch,
        document_summary=document_summary,
        tracked_opportunities=tracked_opportunities,
        documentation_updates=documentation_updates,
    )


@router.get(
    "/demo/dashboard/data",
    response_model=DashboardWorkspaceResponse,
    summary="Load a consolidated stateless demo dashboard payload",
)
def get_demo_dashboard_data() -> DashboardWorkspaceResponse:
    chief_brief = build_demo_chief_brief()
    career_watch = build_demo_career_watch()
    admin_readiness = _admin_from_demo_brief(chief_brief)
    return _workspace_response(
        mode="demo",
        user_key=DEMO_USER_KEY,
        chief_brief=chief_brief,
        admin_readiness=admin_readiness,
        career_watch=career_watch,
        document_summary=chief_brief.document_summary,
        tracked_opportunities=career_watch.tracked_opportunities,
        documentation_updates=chief_brief.documentation_updates,
    )


def _workspace_response(
    *,
    mode: str,
    user_key: str | None,
    chief_brief: ChiefBriefResponse,
    admin_readiness: AdminReadinessResponse,
    career_watch: CareerWatchResponse,
    document_summary: PersonalDocumentSummary | None,
    tracked_opportunities: list[OpportunityRecord],
    documentation_updates: list[DocumentationUpdateCandidate],
) -> DashboardWorkspaceResponse:
    summary_lines = [
        *chief_brief.summary_lines[:2],
        *admin_readiness.summary_lines[:1],
        *career_watch.warnings[:1],
    ]
    warnings = list(dict.fromkeys([
        *chief_brief.warnings,
        *admin_readiness.warnings,
        *career_watch.warnings,
    ]))
    return DashboardWorkspaceResponse(
        mode=mode,
        user_key=user_key,
        summary_lines=[line for line in summary_lines if line],
        chief_brief=chief_brief,
        admin_readiness=admin_readiness,
        career_watch=career_watch,
        document_summary=document_summary,
        tracked_opportunities=tracked_opportunities,
        documentation_updates=documentation_updates,
        warnings=warnings,
    )


def _admin_from_demo_brief(chief_brief: ChiefBriefResponse) -> AdminReadinessResponse:
    document_summary = chief_brief.document_summary
    items = []
    for item in chief_brief.action_items:
        if item.category in {"admin", "fitrep", "documents", "travel"}:
            items.append(
                {
                    "title": item.title,
                    "category": item.category,
                    "priority": item.priority,
                    "due_date": item.due_date,
                    "recommendation": item.recommendation,
                    "source": item.source,
                }
            )
    return AdminReadinessResponse(
        title="Demo admin readiness",
        user_key=DEMO_USER_KEY,
        handoff=chief_brief.handoff,
        summary_lines=[
            "Demo mode shows a synthesized admin slice derived from the Chief/Aide brief.",
            "Use personal mode for real local document, travel, and readiness cues.",
        ],
        items=items[:6],
        document_summary=document_summary,
        warnings=["Demo mode is stateless and read-only."],
    )
