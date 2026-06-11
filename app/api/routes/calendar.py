from collections.abc import Iterator
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.core.security import detect_sensitive_input
from app.schemas.calendar import (
    DrillPrepPlanRequest,
    DrillPrepPlanResponse,
    HandoffReminderPlanRequest,
    HandoffReminderPlanResponse,
)
from app.schemas.session import UserSessionHandoff
from app.services.calendar.drill_detail_extractor import extract_drill_details
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.calendar.planner import DrillPrepPlanner
from app.services.calendar.providers import LocalIcsProvider
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/calendar", tags=["calendar"], dependencies=[LocalApiKeyDependency])

_planner = DrillPrepPlanner()
_ics_provider = LocalIcsProvider()


def get_plan_store() -> Iterator[DrillPrepPlanStore]:
    yield DrillPrepPlanStore(get_settings().drill_plans_storage_dir)


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_handoff_store() -> Iterator[SessionHandoffStore]:
    yield SessionHandoffStore(get_settings().session_handoff_storage_dir)


@router.post("/drill-prep-plan", response_model=DrillPrepPlanResponse)
def create_drill_prep_plan(
    request: DrillPrepPlanRequest,
    store: Annotated[DrillPrepPlanStore, Depends(get_plan_store)],
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> DrillPrepPlanResponse:
    key_event_warnings = _validate_key_events(request)
    extracted_events = []
    warnings: list[str] = [*key_event_warnings]
    for context_id in request.context_ids:
        preview = context_store.read_preview(context_id)
        if preview is None:
            warnings.append(f"Local context {context_id} was not found and was not used.")
            continue
        extracted = extract_drill_details(
            preview,
            source_context_id=context_id,
            default_date=request.drill_date,
        )
        extracted_events.extend(extracted)
        if not extracted:
            warnings.append(f"Local context {context_id} was read but no templated drill events were extracted.")
    plan = _planner.build_plan(
        drill_date=request.drill_date,
        unit_id=request.unit_id,
        include_travel_tasks=request.include_travel_tasks,
        key_events=[*request.key_events, *extracted_events],
        context_ids=request.context_ids,
        local_context_used=bool(extracted_events),
        warnings=warnings,
    )
    return store.save(plan)


@router.get("/drill-prep-plan/{plan_id}", response_model=DrillPrepPlanResponse)
def get_drill_prep_plan(
    plan_id: str,
    store: Annotated[DrillPrepPlanStore, Depends(get_plan_store)],
) -> DrillPrepPlanResponse:
    plan = store.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Unknown drill prep plan: {plan_id}")
    return plan


@router.get("/drill-prep-plan/{plan_id}/ics")
def export_drill_prep_plan(
    plan_id: str,
    store: Annotated[DrillPrepPlanStore, Depends(get_plan_store)],
) -> Response:
    plan = store.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Unknown drill prep plan: {plan_id}")
    return Response(
        content=_ics_provider.export_plan(plan),
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{plan_id}.ics"'},
    )


@router.delete("/drill-prep-plan/{plan_id}", status_code=204)
def delete_drill_prep_plan(
    plan_id: str,
    store: Annotated[DrillPrepPlanStore, Depends(get_plan_store)],
) -> None:
    if not store.delete(plan_id):
        raise HTTPException(status_code=404, detail=f"Unknown drill prep plan: {plan_id}")


@router.post("/handoffs/{user_key}/reminder-plans", response_model=HandoffReminderPlanResponse)
def create_handoff_reminder_plans(
    user_key: str,
    request: HandoffReminderPlanRequest,
    store: Annotated[DrillPrepPlanStore, Depends(get_plan_store)],
    handoff_store: Annotated[SessionHandoffStore, Depends(get_handoff_store)],
) -> HandoffReminderPlanResponse:
    handoff = handoff_store.get(user_key)
    if handoff is None:
        raise HTTPException(status_code=404, detail=f"Unknown handoff: {user_key}")
    drill_dates = _select_drill_dates(handoff, only_future=request.only_future_drills)
    if not drill_dates:
        raise HTTPException(status_code=422, detail="No drill dates are stored for this handoff.")
    plans = [
        store.save(
            _planner.build_plan(
                drill_date=drill_date,
                unit_id=handoff.unit_id,
                include_travel_tasks=request.include_travel_tasks,
                recurring_checks=handoff.recurring_checks,
                recurring_drill_notes=handoff.recurring_drill_notes,
                warnings=["Generated from stored handoff rhythm and recurring checks."],
            )
        )
        for drill_date in drill_dates
    ]
    warnings = []
    if not handoff.recurring_checks and not handoff.recurring_drill_notes:
        warnings.append(
            "No recurring checks or drill notes were stored; only baseline drill-prep tasks were generated."
        )
    return HandoffReminderPlanResponse(
        user_key=user_key,
        generated_plan_ids=[plan.id for plan in plans],
        plans=plans,
        warnings=warnings,
    )


def _validate_key_events(request: DrillPrepPlanRequest) -> list[str]:
    warnings: list[str] = []
    for event in request.key_events:
        if event.classification_label.upper() != "UNCLASSIFIED":
            raise HTTPException(status_code=422, detail="Drill key events must be marked UNCLASSIFIED.")
        text = " ".join(
            value
            for value in [
                event.title,
                event.location or "",
                event.uniform or "",
                event.notes or "",
                " ".join(event.due_outs),
            ]
            if value
        )
        warnings.extend(detect_sensitive_input(text))
    return sorted(set(warnings))


def _select_drill_dates(handoff: UserSessionHandoff, *, only_future: bool) -> list[date]:
    current = datetime.now(UTC).date()
    results = [
        item.drill_date for item in handoff.drill_dates if not only_future or item.drill_date >= current
    ]
    return sorted(dict.fromkeys(results))
