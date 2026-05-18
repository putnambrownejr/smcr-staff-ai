from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.actions import ActionRecord, ActionStatus
from app.schemas.admin import AdminReadinessResponse
from app.schemas.career import CareerWatchResponse
from app.schemas.chief import ChiefActionItem, ChiefBriefRequest, ChiefBriefResponse
from app.schemas.dashboard import AnalystBrief, DailyOpsBrief, DailyOpsEntry, DashboardWorkspaceResponse
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.source_updates import DocumentationUpdateCandidate, UpdateReviewStatus
from app.services.actions.tracker import ActionTracker
from app.services.admin.readiness import AdminReadinessService
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.career.watch import CareerWatchService
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.connectors.travel_case_store import TravelCaseStore
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
        travel_case_store=TravelCaseStore(settings.travel_case_storage_dir),
    )


def get_admin_service(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> AdminReadinessService:
    settings = get_settings()
    return AdminReadinessService(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(store),
        travel_case_store=TravelCaseStore(settings.travel_case_storage_dir),
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


def get_action_tracker() -> Iterator[ActionTracker]:
    settings = get_settings()
    yield ActionTracker(f"{settings.local_context_storage_dir}/actions")


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
    action_tracker: Annotated[ActionTracker, Depends(get_action_tracker)],
    opportunity_tracker: Annotated[OpportunityTracker, Depends(get_opportunity_tracker)],
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> DashboardWorkspaceResponse:
    chief_brief = orchestrator.build_brief(ChiefBriefRequest(user_key=user_key))
    admin_readiness = admin_service.build(user_key)
    career_watch = career_service.build_watch(user_key)
    document_summary = organizer.list_documents()
    tracked_actions = action_tracker.list(user_key=user_key, include_closed=False)[:12]
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
        tracked_actions=tracked_actions,
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
        tracked_actions=[],
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
    tracked_actions: list[ActionRecord],
    tracked_opportunities: list[OpportunityRecord],
    documentation_updates: list[DocumentationUpdateCandidate],
) -> DashboardWorkspaceResponse:
    summary_lines = [
        *chief_brief.next_drill_readiness.summary[:2],
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
        daily_ops_brief=_daily_ops_brief(
            chief_brief=chief_brief,
            admin_readiness=admin_readiness,
            career_watch=career_watch,
            tracked_actions=tracked_actions,
            documentation_updates=documentation_updates,
            document_summary=document_summary,
        ),
        analyst_brief=_analyst_brief(
            chief_brief=chief_brief,
            admin_readiness=admin_readiness,
            career_watch=career_watch,
            documentation_updates=documentation_updates,
            tracked_actions=tracked_actions,
            tracked_opportunities=tracked_opportunities,
            document_summary=document_summary,
        ),
        document_summary=document_summary,
        tracked_actions=tracked_actions,
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


def _daily_ops_brief(
    *,
    chief_brief: ChiefBriefResponse,
    admin_readiness: AdminReadinessResponse,
    career_watch: CareerWatchResponse,
    documentation_updates: list[DocumentationUpdateCandidate],
    tracked_actions: list[ActionRecord],
    document_summary: PersonalDocumentSummary | None,
) -> DailyOpsBrief:
    actions = chief_brief.action_items
    must_do = [_entry_from_action(item) for item in actions if item.priority == "high"][:5]
    if not must_do:
        must_do = [_entry_from_action(item) for item in chief_brief.next_drill_readiness.must_do_before_drill[:3]]
    if not must_do:
        must_do = [_entry_from_action(item) for item in chief_brief.top_priority_items[:3]]
    should_do = [_entry_from_action(item) for item in actions if item.priority == "medium"][:5]
    can_defer = [_entry_from_action(item) for item in actions if item.priority == "low"][:5]
    blocked_entries = [
        _entry_from_tracked_action(item)
        for item in tracked_actions
        if item.status == ActionStatus.blocked
    ][:2]
    active_entries = [
        _entry_from_tracked_action(item)
        for item in tracked_actions
        if item.status in {ActionStatus.open, ActionStatus.in_progress}
    ][:4]
    waiting_entries = [
        _entry_from_tracked_action(item)
        for item in tracked_actions
        if item.status == ActionStatus.waiting
    ][:3]
    must_do = [*must_do, *blocked_entries][:6]
    should_do = [
        *active_entries,
        *should_do,
    ][:6]
    can_defer = [
        *waiting_entries,
        *can_defer,
    ][:6]

    waiting_on: list[str] = []
    if documentation_updates:
        waiting_on.append(
            f"{len(documentation_updates)} documentation update candidate(s) still need review or disposition."
        )
    if career_watch.tracked_opportunities:
        waiting_on.append(
            f"{len(career_watch.tracked_opportunities)} tracked opportunity record(s) need pursue/archive decisions."
        )
    if chief_brief.handoff_is_stale:
        waiting_on.append("Session handoff is stale and should be refreshed before relying on watch items.")
    waiting_on.extend(
        [
            f"{item.title} is waiting on {item.owner or 'an owner'}."
            for item in tracked_actions
            if item.status == ActionStatus.waiting
        ][:3]
    )

    blockers: list[str] = []
    blockers.extend(chief_brief.next_drill_readiness.missing_foundation[:3])
    if document_summary is not None:
        if document_summary.missing_recommended_types:
            blockers.append(
                "Missing recommended local documents: "
                + ", ".join(document_summary.missing_recommended_types[:4])
            )
        if document_summary.expired_count:
            blockers.append(f"{document_summary.expired_count} local document(s) are expired.")
    if any(item.category == "fitrep" for item in admin_readiness.items):
        blockers.append("FitRep watch items exist and still require confirmed support, routing, or suspense checks.")
    blockers.extend(
        [
            f"{item.title} is blocked{f' by {item.owner}' if item.owner else ''}."
            for item in tracked_actions
            if item.status == ActionStatus.blocked
        ][:3]
    )

    leverage_actions = [
        item.title for item in chief_brief.next_drill_readiness.must_do_before_drill[:3]
    ] or [
        item.title for item in chief_brief.top_priority_items[:3]
    ] or [
        "Refresh the session handoff.",
        "Confirm the next drill or admin suspense.",
        "Review source-update or opportunity watch items.",
    ]

    prep_follow_ups = [task.title for plan in chief_brief.drill_plans for task in plan.tasks[:2]][:4]
    if not prep_follow_ups:
        prep_follow_ups = chief_brief.next_drill_readiness.recommended_follow_on_workflows[:3] or [
            "Review the next drill-prep plan.",
            "Confirm travel, uniform, and gear timelines.",
        ]
    prep_follow_ups.extend(
        [
            f"{item.title} -> {item.owner or 'assign owner'}"
            for item in tracked_actions
            if item.status in {ActionStatus.open, ActionStatus.in_progress}
        ][:3]
    )

    return DailyOpsBrief(
        executive_snapshot=chief_brief.summary_lines[:3],
        must_do=must_do,
        should_do=should_do,
        can_defer=can_defer,
        waiting_on=waiting_on,
        blockers=blockers,
        leverage_actions=leverage_actions,
        prep_follow_ups=prep_follow_ups,
    )


def _analyst_brief(
    *,
    chief_brief: ChiefBriefResponse,
    admin_readiness: AdminReadinessResponse,
    career_watch: CareerWatchResponse,
    documentation_updates: list[DocumentationUpdateCandidate],
    tracked_actions: list[ActionRecord],
    tracked_opportunities: list[OpportunityRecord],
    document_summary: PersonalDocumentSummary | None,
) -> AnalystBrief:
    data_quality_notes: list[str] = []
    if document_summary is not None:
        data_quality_notes.extend(
            [
                f"{document_summary.total_documents} local document(s) indexed.",
                f"{document_summary.review_due_count} document(s) due for review.",
                f"{document_summary.expired_count} document(s) expired.",
            ]
        )
        if document_summary.pii_flagged_count:
            data_quality_notes.append(
                f"{document_summary.pii_flagged_count} local document(s) contain detected PII and need care."
            )
    if chief_brief.handoff_is_stale:
        data_quality_notes.append(
            "Session handoff is stale, which lowers confidence in career and admin watch signals."
        )

    kpi_summary = [
        f"{len(chief_brief.action_items)} total action item(s) in the Chief/Aide brief.",
        f"{len(admin_readiness.items)} admin readiness cue(s) currently surfaced.",
        f"{len(career_watch.watch_items)} career watch cue(s) currently surfaced.",
        f"{len(tracked_actions)} tracked POAM/action item(s) currently open.",
        f"{len(tracked_opportunities)} tracked opportunity record(s) in local storage.",
    ]

    anomalies: list[str] = []
    if documentation_updates:
        anomalies.append(
            f"{len(documentation_updates)} source update candidate(s) may indicate stale doctrine or admin references."
        )
    if document_summary is not None and document_summary.missing_recommended_types:
        anomalies.append("Core local support documents are incomplete for the current profile.")
    if chief_brief.handoff is None:
        anomalies.append("No session handoff is present, which makes the dashboard less personalized.")
    blocked_actions = [item for item in tracked_actions if item.status == ActionStatus.blocked]
    if blocked_actions:
        anomalies.append(f"{len(blocked_actions)} tracked action item(s) are blocked.")

    likely_causes = [
        "Reserve workflows are fragmented across local notes, watch items, and manually tracked opportunities.",
        "Action ownership and suspense discipline are still partly local and manually maintained.",
        "Source freshness depends on scans and human review rather than automatic authoritative reconciliation.",
    ]
    if documentation_updates:
        likely_causes.append(
            "Recent MARADMIN or MCPEL change signals have not yet been reviewed into the local corpus."
        )

    assumptions = [
        "Local uploads are advisory context only and are not authoritative doctrine or official records.",
        "Tracked opportunities do not establish eligibility, approval, or final availability.",
        "Unreviewed source updates should be treated as warnings, not confirmed changes.",
    ]

    follow_up_checks = [
        "Run or review document/source freshness checks before relying on older policy summaries.",
        "Refresh the handoff when PME, FitRep, or billet interests change.",
        "Confirm document gaps and expirations against real user-owned records.",
    ]
    if tracked_opportunities:
        follow_up_checks.append("Compare tracked opportunities against MOS, rank, geography, and timing before acting.")
    if tracked_actions:
        follow_up_checks.append("Review blocked and waiting action items for owner, suspense, and next-move clarity.")

    return AnalystBrief(
        executive_summary=chief_brief.summary_lines[:2] or ["Dashboard loaded with current local advisory context."],
        data_quality_notes=data_quality_notes,
        kpi_summary=kpi_summary,
        anomalies=anomalies,
        likely_causes=likely_causes,
        assumptions=assumptions,
        follow_up_checks=follow_up_checks,
    )


def _entry_from_action(item: ChiefActionItem) -> DailyOpsEntry:
    return DailyOpsEntry(
        title=item.title,
        detail=item.recommendation,
        category=item.category,
        priority=item.priority,
        due_date=item.due_date.isoformat() if item.due_date else None,
    )


def _entry_from_tracked_action(item: ActionRecord) -> DailyOpsEntry:
    detail_parts = [
        item.description or "",
        f"Owner: {item.owner}" if item.owner else "",
        f"Status: {item.status.value}",
        f"Suspense: {item.suspense_date.isoformat()}" if item.suspense_date else "",
    ]
    return DailyOpsEntry(
        title=item.title,
        detail=" | ".join(part for part in detail_parts if part),
        category=item.category.value,
        priority=item.priority.value,
        due_date=item.suspense_date.isoformat() if item.suspense_date else None,
    )
