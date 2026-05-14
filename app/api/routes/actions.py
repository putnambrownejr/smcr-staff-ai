from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.actions import (
    ActionBundleTrackRequest,
    ActionBundleTrackResponse,
    ActionFollowUpRequest,
    ActionFollowUpResponse,
    ActionFollowUpResult,
    ActionLinkRequest,
    ActionPromoteRequest,
    ActionPromoteResponse,
    ActionRecord,
    ActionStatus,
    ActionTrackRequest,
    ActionTrackResponse,
    ActionUpdateRequest,
    AnnualTrainingActionBundleRequest,
    CorrespondenceActionBundleRequest,
    RangePackageActionBundleRequest,
)
from app.schemas.chief import ChiefBriefRequest
from app.schemas.context import LocalContextMetadata
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.services.actions.bundle_builder import ActionBundleBuilder
from app.services.actions.follow_up import ActionFollowUpProcessor
from app.services.actions.promoter import ActionPromoter
from app.services.actions.tracker import ActionTracker
from app.services.admin.readiness import AdminReadinessService
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.personnel.correspondence_converter import CorrespondenceConverter
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore
from app.services.training.event_planner import AnnualTrainingPlanner, RangePackagePlanner

router = APIRouter(prefix="/actions", tags=["action tracker"], dependencies=[LocalApiKeyDependency])
_promoter = ActionPromoter()
_bundle_builder = ActionBundleBuilder()
_annual_training_planner = AnnualTrainingPlanner()
_range_package_planner = RangePackagePlanner()
_correspondence_converter = CorrespondenceConverter()
_follow_up_processor = ActionFollowUpProcessor()
SEED_DIR = Path("data/seed")


def get_tracker() -> Iterator[ActionTracker]:
    settings = get_settings()
    yield ActionTracker(f"{settings.local_context_storage_dir}/actions")


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_update_store() -> Iterator[DocumentUpdateStore]:
    settings = get_settings()
    yield DocumentUpdateStore(f"{settings.local_context_storage_dir}/document_updates")


def get_orchestrator(
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> ChiefAideOrchestrator:
    settings = get_settings()
    return ChiefAideOrchestrator(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(context_store),
        drill_plan_store=DrillPrepPlanStore(f"{settings.local_context_storage_dir}/drill_plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(SEED_DIR / "reading_list.example.yaml"),
        document_update_store=update_store,
        opportunity_tracker=OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities"),
    )


def get_admin_readiness_service(
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> AdminReadinessService:
    settings = get_settings()
    return AdminReadinessService(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(context_store),
    )


@router.get("", response_model=list[ActionRecord])
def list_actions(
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
    user_key: str | None = None,
    status: ActionStatus | None = None,
    include_closed: bool = False,
) -> list[ActionRecord]:
    return tracker.list(user_key=user_key, status=status, include_closed=include_closed)


@router.post("/track", response_model=ActionTrackResponse)
def track_actions(
    request: ActionTrackRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionTrackResponse:
    tracked = tracker.track(request.actions)
    return ActionTrackResponse(tracked=tracked, message="Tracked POAM and action items locally.")


@router.post("/promote", response_model=ActionPromoteResponse)
def promote_actions(
    request: ActionPromoteRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> ActionPromoteResponse:
    for link in request.shared_links:
        _validate_link_target(link, context_store, update_store)
    for item in request.items:
        for link in item.links:
            _validate_link_target(link, context_store, update_store)

    action_requests = _promoter.build(request)
    tracked = tracker.track(action_requests)
    linked_records: list[ActionRecord] = []
    for record, item in zip(tracked, request.items, strict=False):
        current = record
        for link in request.shared_links:
            updated = tracker.add_link(current.action_id, link)
            if updated is not None:
                current = updated
        for link in item.links:
            updated = tracker.add_link(current.action_id, link)
            if updated is not None:
                current = updated
        linked_records.append(current)
    return ActionPromoteResponse(
        tracked=linked_records,
        summary_lines=[
            f"Promoted {len(linked_records)} generated item(s) into tracked actions.",
            "Category, priority, and suspense may be inferred from source text and should be reviewed.",
        ],
        message="Promoted generated due-outs/checklists into local action tracking.",
    )


@router.post("/from-chief-brief", response_model=ActionBundleTrackResponse)
def track_actions_from_chief_brief(
    request: ChiefBriefRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
    orchestrator: Annotated[ChiefAideOrchestrator, Depends(get_orchestrator)],
) -> ActionBundleTrackResponse:
    brief = orchestrator.build_brief(request)
    tracked = tracker.track(_bundle_builder.from_chief_brief(brief))
    return _bundle_response(brief.title, tracked, len(brief.action_items), "chief brief")


@router.post("/from-admin-readiness/{user_key}", response_model=ActionBundleTrackResponse)
def track_actions_from_admin_readiness(
    user_key: str,
    request: ActionBundleTrackRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
    service: Annotated[AdminReadinessService, Depends(get_admin_readiness_service)],
) -> ActionBundleTrackResponse:
    readiness = service.build(user_key)
    tracked = tracker.track(_bundle_builder.from_admin_readiness(readiness))
    return _bundle_response(readiness.title, tracked, len(readiness.items), "admin readiness")


@router.post("/from-annual-training-plan", response_model=ActionBundleTrackResponse)
def track_actions_from_annual_training_plan(
    request: AnnualTrainingActionBundleRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionBundleTrackResponse:
    plan = _annual_training_planner.build(request.plan)
    tracked = tracker.track(
        _bundle_builder.from_annual_training_plan(
            plan,
            user_key=request.options.user_key,
            owner=request.options.owner,
        )
    )
    return _bundle_response(plan.title, tracked, len(tracked), "annual training plan")


@router.post("/from-correspondence-conversion", response_model=ActionBundleTrackResponse)
def track_actions_from_correspondence_conversion(
    request: CorrespondenceActionBundleRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionBundleTrackResponse:
    draft = _correspondence_converter.build(request.draft)
    tracked = tracker.track(
        _bundle_builder.from_correspondence_conversion(
            draft,
            user_key=request.options.user_key,
            owner=request.options.owner,
        )
    )
    return _bundle_response(draft.title, tracked, len(tracked), "correspondence conversion")


@router.post("/from-range-package", response_model=ActionBundleTrackResponse)
def track_actions_from_range_package(
    request: RangePackageActionBundleRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionBundleTrackResponse:
    package = _range_package_planner.build(request.package)
    tracked = tracker.track(
        _bundle_builder.from_range_package(
            package,
            user_key=request.options.user_key,
            owner=request.options.owner,
        )
    )
    return _bundle_response(package.title, tracked, len(tracked), "range package")


@router.post("/follow-up", response_model=ActionFollowUpResponse)
def apply_action_follow_up(
    request: ActionFollowUpRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionFollowUpResponse:
    updated = _follow_up_processor.apply(tracker, request)
    return ActionFollowUpResponse(
        updated=[
            ActionFollowUpResult(action_id=item[0], title=item[1], status=item[2], notes=item[3]) for item in updated
        ],
        summary_lines=[
            f"Updated {len(updated)} action(s) from follow-up notes.",
            "Statuses may be inferred from note language unless you set one explicitly.",
        ],
        message="Applied follow-up notes to tracked actions.",
    )


@router.patch("/{action_id}", response_model=ActionRecord)
def update_action(
    action_id: str,
    request: ActionUpdateRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionRecord:
    record = tracker.update(action_id, request)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown action item: {action_id}")
    return record


@router.post("/{action_id}/links", response_model=ActionRecord)
def add_action_link(
    action_id: str,
    request: ActionLinkRequest,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> ActionRecord:
    _validate_link_target(request, context_store, update_store)
    record = tracker.add_link(action_id, request)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown action item: {action_id}")
    return record


@router.delete("/{action_id}/links/{link_id}", response_model=ActionRecord)
def remove_action_link(
    action_id: str,
    link_id: str,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> ActionRecord:
    record = tracker.remove_link(action_id, link_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown action item or link: {action_id}/{link_id}")
    return record


@router.delete("/{action_id}", status_code=204)
def delete_action(
    action_id: str,
    tracker: Annotated[ActionTracker, Depends(get_tracker)],
) -> None:
    if not tracker.delete(action_id):
        raise HTTPException(status_code=404, detail=f"Unknown action item: {action_id}")


def _validate_link_target(
    request: ActionLinkRequest,
    context_store: LocalContextStore,
    update_store: DocumentUpdateStore,
) -> LocalContextMetadata | DocumentationUpdateCandidate | None:
    if request.link_type.value == "url":
        if request.url is None:
            raise HTTPException(status_code=422, detail="URL links require a url.")
        return None
    if request.link_type.value == "local_context":
        if request.target_id is None:
            raise HTTPException(status_code=422, detail="Local context links require target_id.")
        item = context_store.get(request.target_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"Unknown local context item: {request.target_id}")
        return item
    if request.target_id is None:
        raise HTTPException(status_code=422, detail="Documentation update links require target_id.")
    candidate = update_store.get(request.target_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Unknown documentation update candidate: {request.target_id}")
    return candidate


def _bundle_response(
    source_title: str,
    tracked: list[ActionRecord],
    source_count: int,
    source_kind: str,
) -> ActionBundleTrackResponse:
    return ActionBundleTrackResponse(
        source_title=source_title,
        tracked=tracked,
        summary_lines=[
            f"Promoted {len(tracked)} action(s) from {source_kind}.",
            f"Source contained {source_count} item(s) considered for tracking.",
        ],
        message=f"Tracked actions generated from {source_kind}.",
    )
