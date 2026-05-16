from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta

from app.core.security import DEFAULT_WARNINGS
from app.schemas.calendar import DrillPrepPlanResponse
from app.schemas.chief import ChiefActionItem, ChiefBriefRequest, ChiefBriefResponse, NextDrillReadiness
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.session import DrillDateRecord, FitrepReminder, PmeStatus, RecurringCheck, UserSessionHandoff
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.schemas.user_context import ActiveUserContext
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.document_update_monitor import DocumentUpdateMonitor
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.active_context_store import ActiveUserContextStore
from app.services.session.handoff_store import SessionHandoffStore


class ChiefAideOrchestrator:
    def __init__(
        self,
        handoff_store: SessionHandoffStore,
        document_organizer: PersonalDocumentOrganizer,
        drill_plan_store: DrillPrepPlanStore,
        reading_catalog: ReadingListCatalogService,
        document_update_store: DocumentUpdateStore | None = None,
        opportunity_tracker: OpportunityTracker | None = None,
        active_context_store: ActiveUserContextStore | None = None,
    ) -> None:
        self.handoff_store = handoff_store
        self.document_organizer = document_organizer
        self.drill_plan_store = drill_plan_store
        self.reading_catalog = reading_catalog
        self.document_update_store = document_update_store or DocumentUpdateStore()
        self.opportunity_tracker = opportunity_tracker or OpportunityTracker()
        self.active_context_store = active_context_store

    def build_brief(self, request: ChiefBriefRequest) -> ChiefBriefResponse:
        handoff = self.handoff_store.get(request.user_key) if request.user_key else None
        active_user_context = self.active_context_store.get(request.user_key) if (
            request.user_key and self.active_context_store is not None
        ) else None
        handoff_is_stale = _handoff_is_stale(handoff)
        document_summary = self.document_organizer.list_documents() if request.include_personal_documents else None
        drill_plans = self.drill_plan_store.list() if request.include_drill_plans else []
        opportunities = self.opportunity_tracker.list()
        updates = self.document_update_store.list()
        if request.maradmin_records:
            scanned_updates = DocumentUpdateMonitor().scan_maradmin_records(request.maradmin_records).candidates
            updates = self.document_update_store.save_many(scanned_updates)
        action_items = _dedupe_actions(
            [
            *_handoff_actions(handoff),
            *_personal_rhythm_actions(handoff, drill_plans),
            *_document_actions(document_summary, handoff),
            *_opportunity_actions(opportunities, handoff),
            *_career_actions(handoff),
            *_drill_actions(drill_plans),
            *_update_actions(updates),
            ]
        )
        sorted_actions = _sort_actions(action_items)
        next_drill_readiness = _next_drill_readiness(
            handoff=handoff,
            handoff_is_stale=handoff_is_stale,
            drill_plans=drill_plans,
            document_summary=document_summary,
            updates=updates,
            actions=sorted_actions,
            user_key=request.user_key,
        )
        return ChiefBriefResponse(
            title="Chief of Staff / Aide de Camp triage brief",
            user_key=request.user_key,
            handoff=handoff,
            active_user_context=active_user_context,
            handoff_is_stale=handoff_is_stale,
            next_drill_readiness=next_drill_readiness,
            summary_lines=_summary_lines(
                handoff=handoff,
                active_user_context=active_user_context,
                handoff_is_stale=handoff_is_stale,
                actions=sorted_actions,
                updates=updates,
                drill_plans=drill_plans,
                document_summary=document_summary,
                next_drill_readiness=next_drill_readiness,
            ),
            action_items=sorted_actions,
            top_priority_items=_top_priority_items(sorted_actions),
            document_summary=document_summary,
            drill_plans=drill_plans,
            documentation_updates=updates,
            reading_recommendations=_reading_recommendations(self.reading_catalog),
            recommended_courses=_recommended_courses(handoff),
            warnings=[
                *DEFAULT_WARNINGS,
                *(
                    ["Session handoff may be stale. Refresh PME, FitRep, and admin watch items before relying on it."]
                    if handoff_is_stale
                    else []
                ),
                "This brief is advisory and should be reviewed by the user before action.",
                "Local documents are user-provided context and are not official source authority.",
            ],
        )


def _handoff_actions(handoff: UserSessionHandoff | None) -> list[ChiefActionItem]:
    if handoff is None:
        return [
            ChiefActionItem(
                title="Create or update session handoff",
                category="handoff",
                priority="medium",
                recommendation="Add rank, MOS, billet, PME, FitRep, and recurring admin watch items.",
            )
        ]
    actions: list[ChiefActionItem] = []
    for pme in handoff.pme:
        actions.append(_pme_action(pme))
    for fitrep in handoff.fitreps:
        actions.append(_fitrep_action(fitrep))
    for item in handoff.admin_watch_items:
        actions.append(
            ChiefActionItem(
                title=item,
                category="admin",
                priority="medium",
                recommendation="Review this admin watch item and assign a next suspense if needed.",
            )
        )
    if not handoff.drill_dates:
        actions.append(
            ChiefActionItem(
                title="Add annual drill schedule to session handoff",
                category="drill",
                priority="medium",
                recommendation=(
                    "Store the upcoming drill dates so recurring prep reminders can anchor to a real unit rhythm."
                ),
            )
        )
    return actions


def _personal_rhythm_actions(
    handoff: UserSessionHandoff | None,
    drill_plans: list[DrillPrepPlanResponse],
) -> list[ChiefActionItem]:
    if handoff is None:
        return []
    actions: list[ChiefActionItem] = []
    anchor = _next_drill_anchor(handoff.drill_dates, drill_plans)
    for note in handoff.recurring_drill_notes:
        actions.append(
            ChiefActionItem(
                title=f"Recurring drill reminder: {note}",
                category="drill_rhythm",
                priority="medium" if anchor is not None else "low",
                due_date=anchor,
                source="session_handoff",
                recommendation=(
                    "Keep this in the pre-drill routine and confirm it still belongs in the standing checklist."
                ),
            )
        )
    for check in handoff.recurring_checks:
        actions.append(
            ChiefActionItem(
                title=f"Recurring {check.category} check: {check.title}",
                category=check.category,
                priority=_recurring_priority(check, anchor),
                due_date=_recurring_due_date(check, anchor),
                source="session_handoff",
                recommendation=_recurring_recommendation(check),
            )
        )
    return actions


def _pme_action(pme: PmeStatus) -> ChiefActionItem:
    return ChiefActionItem(
        title=f"PME: {pme.program} is {pme.status}",
        category="pme",
        priority=_priority(pme.due_date),
        due_date=pme.due_date,
        source="session_handoff",
        recommendation="Verify current PME requirements and schedule the next concrete step.",
    )


def _fitrep_action(fitrep: FitrepReminder) -> ChiefActionItem:
    return ChiefActionItem(
        title=f"FitRep: {fitrep.occasion}",
        category="fitrep",
        priority=_priority(fitrep.due_date),
        due_date=fitrep.due_date,
        source="session_handoff",
        recommendation="Confirm reporting occasion, RS/RO timeline, and required inputs.",
    )


def _document_actions(
    document_summary: PersonalDocumentSummary | None,
    handoff: UserSessionHandoff | None,
) -> list[ChiefActionItem]:
    if document_summary is None:
        return []
    actions: list[ChiefActionItem] = []
    if document_summary.total_documents == 0:
        actions.append(
            ChiefActionItem(
                title="Add key personal USMC documents",
                category="documents",
                priority="medium",
                recommendation="Upload local references such as RQS, BIO, orders, receipts, and PME certificates.",
            )
        )
    if document_summary.pii_flagged_count:
        actions.append(
            ChiefActionItem(
                title="Review PII-flagged local documents",
                category="documents",
                priority="high",
                recommendation="Confirm these records are necessary, local-only, and safe to retain.",
            )
        )
    document_types = {record.document_type.value for record in document_summary.records}
    missing_items = [
        ("bio", "Add a current BIO reference", "Upload a local BIO draft or reference for quick staff context."),
        (
            "orders",
            "Add current orders reference",
            "Store current orders locally so drill and travel workflows can reference them.",
        ),
        (
            "pme_certificate",
            "Add PME certificate reference",
            "Store PME completion references locally to support career and readiness tracking.",
        ),
    ]
    for document_type, title, recommendation in missing_items:
        if document_type not in document_types:
            actions.append(
                ChiefActionItem(
                    title=title,
                    category="documents",
                    priority="low",
                    recommendation=recommendation,
                )
            )
    if handoff is not None and handoff.rqs_context_id is None and "rqs" not in document_types:
        actions.append(
            ChiefActionItem(
                title="Add RQS reference",
                category="documents",
                priority="medium",
                recommendation="Upload a local RQS reference or link it in the handoff for career tracking.",
            )
        )
    if handoff is not None and handoff.bio_context_id is None and "bio" in document_types:
        actions.append(
            ChiefActionItem(
                title="Link BIO reference in handoff",
                category="handoff",
                priority="low",
                recommendation=(
                    "Populate bio_context_id in the session handoff so the Chief brief can track it explicitly."
                ),
            )
        )
    return actions


def _drill_actions(drill_plans: list[DrillPrepPlanResponse]) -> list[ChiefActionItem]:
    return [
        ChiefActionItem(
            title=f"Review drill plan for {plan.drill_date.isoformat()}",
            category="drill",
            priority=_priority(plan.drill_date),
            due_date=plan.drill_date,
            source=plan.id,
            recommendation="Verify key events, due-outs, uniform, travel, and DTS reminders.",
        )
        for plan in drill_plans[:3]
    ]


def _opportunity_actions(
    opportunities: Sequence[OpportunityRecord],
    handoff: UserSessionHandoff | None,
) -> list[ChiefActionItem]:
    actions = [
        ChiefActionItem(
            title=f"Career opportunity ({opportunity.opportunity_type}): {opportunity.title}",
            category="career",
            priority=_priority(opportunity.due_date),
            due_date=opportunity.due_date,
            source=opportunity.source_url,
            recommendation="Review fit, confirm eligibility, and decide whether to pursue or archive this opportunity.",
        )
        for opportunity in opportunities[:5]
        if opportunity.tracked
    ]
    if handoff is not None:
        actions.extend(
            ChiefActionItem(
                title=f"Career opportunity ({opportunity.opportunity_type}): {opportunity.title}",
                category="career",
                priority=_priority(opportunity.due_date),
                due_date=opportunity.due_date,
                source=opportunity.source_url,
                recommendation="Review fit and add next action or decision note to the handoff.",
            )
            for opportunity in handoff.career_opportunities
        )
    return actions


def _career_actions(handoff: UserSessionHandoff | None) -> list[ChiefActionItem]:
    if handoff is None:
        return []
    actions = [
        ChiefActionItem(
            title=f"Career trend: {trend.label}",
            category="career",
            priority="medium",
            source="session_handoff",
            recommendation=trend.recommended_action or "Review this trend and convert it into a concrete next step.",
        )
        for trend in handoff.career_trends
    ]
    actions.extend(
        ChiefActionItem(
            title=f"Course recommendation: {course}",
            category="career",
            priority="low",
            source="session_handoff",
            recommendation="Decide whether to enroll, defer, or remove this course recommendation.",
        )
        for course in handoff.recommended_courses
    )
    return actions


def _update_actions(updates: list[DocumentationUpdateCandidate]) -> list[ChiefActionItem]:
    return [
        ChiefActionItem(
            title=f"Source update ({update.review_status}): {update.tracked_title}",
            category="source_updates",
            priority=_update_priority(update),
            source=update.trigger_url,
            recommendation="Verify the current official source before relying on stored summaries or citations.",
        )
        for update in updates
        if update.review_status != "ignored"
    ]


def _reading_recommendations(catalog: ReadingListCatalogService) -> list[str]:
    books = catalog.list_books(open_source_only=True)
    return [book.title for book in books[:3]]


def _recommended_courses(handoff: UserSessionHandoff | None) -> list[str]:
    if handoff is None:
        return []
    ordered: list[str] = []
    for pme in handoff.pme:
        ordered.append(f"PME follow-up: {pme.program}")
    ordered.extend(handoff.recommended_courses)
    return _dedupe_strings(ordered)[:5]


def _handoff_is_stale(handoff: UserSessionHandoff | None) -> bool:
    if handoff is None:
        return False
    return handoff.updated_at < datetime.now(UTC) - timedelta(days=30)


def _sort_actions(actions: list[ChiefActionItem]) -> list[ChiefActionItem]:
    priority_order = {"high": 0, "medium": 1, "low": 2}

    def sort_key(action: ChiefActionItem) -> tuple[int, date]:
        fallback_date = date.max
        return (priority_order.get(action.priority, 3), action.due_date or fallback_date)

    return sorted(actions, key=sort_key)


def _top_priority_items(actions: list[ChiefActionItem]) -> list[ChiefActionItem]:
    return [item for item in actions if item.priority in {"high", "medium"}][:5]


def _summary_lines(
    handoff: UserSessionHandoff | None,
    active_user_context: ActiveUserContext | None,
    handoff_is_stale: bool,
    actions: list[ChiefActionItem],
    updates: list[DocumentationUpdateCandidate],
    drill_plans: list[DrillPrepPlanResponse],
    document_summary: PersonalDocumentSummary | None,
    next_drill_readiness: NextDrillReadiness,
) -> list[str]:
    lines: list[str] = []
    lines.append(next_drill_readiness.readiness_posture)
    if active_user_context is not None:
        active_bits = [
            item
            for item in [active_user_context.unit_name, active_user_context.unit_type, active_user_context.unit_family]
            if item
        ]
        if active_bits:
            lines.append("Active local operating context: " + " / ".join(active_bits) + ".")
    if handoff is None:
        lines.append("No session handoff is stored yet, so the brief is operating with limited user context.")
    elif handoff_is_stale:
        lines.append("Session handoff is stale and should be refreshed before relying on PME, FitRep, or admin notes.")
    else:
        lines.append("Session handoff is current enough to support drill, admin, and career reminders.")
    if drill_plans:
        lines.append(f"{len(drill_plans)} stored drill plan(s) are in view for near-term prep.")
    elif handoff is not None and handoff.drill_dates:
        lines.append(f"{len(handoff.drill_dates)} annual drill date(s) are stored for recurring prep reminders.")
    if handoff is not None and handoff.recurring_checks:
        lines.append(f"{len(handoff.recurring_checks)} recurring readiness/admin check(s) are tracked in the handoff.")
    new_updates = [update for update in updates if update.review_status == "new"]
    if new_updates:
        lines.append(f"{len(new_updates)} documentation update candidate(s) need review against official sources.")
    if document_summary is not None and document_summary.missing_recommended_types:
        lines.append(
            "Missing recommended local references: " + ", ".join(document_summary.missing_recommended_types[:4]) + "."
        )
    high_priority = [item for item in actions if item.priority == "high"]
    if high_priority:
        lines.append(f"{len(high_priority)} high-priority item(s) should be handled first.")
    return lines


def _next_drill_readiness(
    *,
    handoff: UserSessionHandoff | None,
    handoff_is_stale: bool,
    drill_plans: list[DrillPrepPlanResponse],
    document_summary: PersonalDocumentSummary | None,
    updates: list[DocumentationUpdateCandidate],
    actions: list[ChiefActionItem],
    user_key: str | None,
) -> NextDrillReadiness:
    anchor = _next_drill_anchor(handoff.drill_dates if handoff is not None else [], drill_plans)
    must_do = [
        item
        for item in actions
        if item.priority == "high" or item.category in {"drill", "drill_rhythm", "travel"}
    ][:6]

    likely_friction_points: list[str] = []
    if handoff_is_stale:
        likely_friction_points.append(
            "Session handoff is stale, so drill/admin continuity may be weaker than the stored notes suggest."
        )
    if handoff is not None and not handoff.drill_dates:
        likely_friction_points.append("No annual drill schedule is stored, which weakens reminder timing.")
    if not drill_plans and anchor is not None:
        likely_friction_points.append("A drill date exists, but no saved drill-prep plan is attached to it yet.")
    if any(item.category == "travel" for item in actions):
        likely_friction_points.append(
            "Travel-admin follow-through is still a likely point of friction before or after drill."
        )
    if any(item.category == "source_updates" for item in actions):
        likely_friction_points.append(
            "Some source-backed references may be stale until update candidates are reviewed."
        )

    missing_foundation: list[str] = []
    if handoff is None:
        missing_foundation.append("No session handoff exists yet.")
    if document_summary is not None:
        for item in document_summary.missing_recommended_types[:4]:
            missing_foundation.append(f"Missing recommended local reference: {item}.")
    if handoff is not None and handoff.rqs_context_id is None:
        missing_foundation.append("No linked RQS reference is present in the handoff.")
    if handoff is not None and handoff.bio_context_id is None:
        missing_foundation.append("No linked BIO reference is present in the handoff.")

    standing_rhythm: list[str] = []
    if handoff is not None:
        standing_rhythm.extend(f"Recurring note: {note}" for note in handoff.recurring_drill_notes[:3])
        standing_rhythm.extend(
            f"Recurring {check.category} check: {check.title}" for check in handoff.recurring_checks[:4]
        )
    if not standing_rhythm:
        standing_rhythm = [
            "Confirm next drill date, uniform, and travel-admin suspense.",
            "Review readiness, training, and admin loose ends before release.",
        ]

    workflow_user = user_key or "your-user-key"
    recommended_follow_on_workflows = [
        f"POST /calendar/handoffs/{workflow_user}/reminder-plans",
        f"GET /admin/readiness/{workflow_user}",
        f"GET /career/watch/{workflow_user}",
    ]
    if anchor is not None or drill_plans:
        recommended_follow_on_workflows.append("POST /planning/staff-package")

    summary = []
    if anchor is not None:
        summary.append(f"Next drill anchor: {anchor.isoformat()}.")
    if must_do:
        summary.append(f"{len(must_do)} action(s) are in the immediate pre-drill lane.")
    if missing_foundation:
        summary.append("Foundational context is still incomplete for at least one readiness lane.")
    if updates:
        summary.append("Source freshness still needs human review before some references are treated as current.")

    posture = _readiness_posture(
        anchor=anchor,
        handoff=handoff,
        handoff_is_stale=handoff_is_stale,
        missing_foundation=missing_foundation,
        updates=updates,
        must_do=must_do,
    )
    decisive_action = _decisive_action(
        handoff=handoff,
        anchor=anchor,
        must_do=must_do,
        missing_foundation=missing_foundation,
        handoff_is_stale=handoff_is_stale,
    )
    this_week_focus = _this_week_focus(
        must_do=must_do,
        missing_foundation=missing_foundation,
        likely_friction_points=likely_friction_points,
    )
    ready_if = _ready_if(
        anchor=anchor,
        handoff=handoff,
        handoff_is_stale=handoff_is_stale,
        missing_foundation=missing_foundation,
        updates=updates,
        must_do=must_do,
    )
    return NextDrillReadiness(
        anchor_drill_date=anchor,
        readiness_posture=posture,
        summary=summary,
        decisive_action=decisive_action,
        this_week_focus=this_week_focus,
        must_do_before_drill=must_do,
        ready_if=ready_if,
        likely_friction_points=likely_friction_points,
        missing_foundation=missing_foundation,
        standing_rhythm=standing_rhythm[:6],
        recommended_follow_on_workflows=recommended_follow_on_workflows,
    )


def _readiness_posture(
    *,
    anchor: date | None,
    handoff: UserSessionHandoff | None,
    handoff_is_stale: bool,
    missing_foundation: list[str],
    updates: list[DocumentationUpdateCandidate],
    must_do: list[ChiefActionItem],
) -> str:
    if handoff is None:
        return "Next-drill readiness posture: weak foundation. Build the handoff and rhythm before trusting the brief."
    if handoff_is_stale:
        return "Next-drill readiness posture: degraded by stale continuity. Refresh the handoff before relying on it."
    if missing_foundation:
        return "Next-drill readiness posture: partially built. Core context or documents are still missing."
    if anchor is None:
        return "Next-drill readiness posture: rhythm exists, but the next drill anchor is not yet explicit."
    if any(item.priority == "high" for item in must_do):
        return "Next-drill readiness posture: active. The rhythm is present, but several items need attention now."
    if any(update.review_status == "new" for update in updates):
        return "Next-drill readiness posture: mostly set, but source freshness still needs review."
    return "Next-drill readiness posture: on track. Use the brief to maintain rhythm and close the remaining gaps."


def _decisive_action(
    *,
    handoff: UserSessionHandoff | None,
    anchor: date | None,
    must_do: list[ChiefActionItem],
    missing_foundation: list[str],
    handoff_is_stale: bool,
) -> str:
    if handoff is None:
        return "Create the session handoff and anchor the next drill before trusting any downstream reminders."
    if handoff_is_stale:
        return "Refresh the stale handoff now so PME, admin, and drill reminders stop drifting on bad continuity."
    if missing_foundation:
        return "Close the missing foundation items first so the rest of the brief is operating on real context."
    if must_do:
        top = must_do[0]
        return f"Handle this first: {top.title}. {top.recommendation}"
    if anchor is None:
        return "Store or confirm the next drill anchor so the standing rhythm has a real timeline."
    return "Use this week to clear small friction before it hardens into a drill-weekend problem."


def _this_week_focus(
    *,
    must_do: list[ChiefActionItem],
    missing_foundation: list[str],
    likely_friction_points: list[str],
) -> list[str]:
    focus = [item.title for item in must_do[:3]]
    if not focus:
        focus.extend(missing_foundation[:2])
    if len(focus) < 3:
        focus.extend(likely_friction_points[: 3 - len(focus)])
    return focus[:3]


def _ready_if(
    *,
    anchor: date | None,
    handoff: UserSessionHandoff | None,
    handoff_is_stale: bool,
    missing_foundation: list[str],
    updates: list[DocumentationUpdateCandidate],
    must_do: list[ChiefActionItem],
) -> list[str]:
    checks: list[str] = []
    checks.append(
        "The next drill is anchored to a real date and the standing reminder rhythm is aligned to it."
        if anchor is not None
        else "The next drill anchor still needs to be stored or confirmed."
    )
    checks.append(
        "Session continuity is current enough to trust the admin, PME, and drill watch items."
        if handoff is not None and not handoff_is_stale
        else "Session continuity still needs to be built or refreshed."
    )
    checks.append(
        "Core local context and documents are present for the next drill cycle."
        if not missing_foundation
        else "Core local context or documents are still missing."
    )
    checks.append(
        "High-priority pre-drill items have owners and near-term follow-through."
        if not any(item.priority == "high" for item in must_do)
        else "At least one high-priority pre-drill item still needs direct attention."
    )
    checks.append(
        "Source-backed references are current enough for routine use."
        if not any(update.review_status == "new" for update in updates)
        else "Source freshness still needs human review before some references are treated as current."
    )
    return checks


def _priority(due_date: date | None) -> str:
    if due_date is None:
        return "medium"
    days = (due_date - datetime.now(UTC).date()).days
    if days < 0:
        return "high"
    if days <= 14:
        return "high"
    if days <= 45:
        return "medium"
    return "low"


def _update_priority(update: DocumentationUpdateCandidate) -> str:
    if update.review_status == "new":
        return "high" if update.confidence == "high" else "medium"
    if update.review_status == "reviewed":
        return "medium"
    return "low"


def _dedupe_actions(actions: list[ChiefActionItem]) -> list[ChiefActionItem]:
    seen: set[str] = set()
    result: list[ChiefActionItem] = []
    for action in actions:
        key = "|".join(
            [
                action.category.lower(),
                action.title.lower(),
                (action.source or "").lower(),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(action)
    return result


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _next_drill_anchor(
    drill_dates: list[DrillDateRecord],
    drill_plans: list[DrillPrepPlanResponse],
) -> date | None:
    today = datetime.now(UTC).date()
    candidates = [plan.drill_date for plan in drill_plans if plan.drill_date >= today]
    candidates.extend(item.drill_date for item in drill_dates if item.drill_date >= today)
    return min(candidates) if candidates else None


def _recurring_due_date(check: RecurringCheck, anchor: date | None) -> date | None:
    if anchor is None:
        return None
    if check.cadence in {"each_drill", "pre_drill", "post_drill"}:
        offset = check.due_offset_days or 0
        return anchor + timedelta(days=offset)
    return None


def _recurring_priority(check: RecurringCheck, anchor: date | None) -> str:
    if check.category in {"travel", "finance"}:
        return "medium"
    if anchor is not None and check.cadence in {"each_drill", "pre_drill", "post_drill"}:
        return _priority(_recurring_due_date(check, anchor))
    return "low"


def _recurring_recommendation(check: RecurringCheck) -> str:
    if check.category == "finance":
        return "Confirm this recurring finance/admin check still has an owner and a realistic review cadence."
    if check.category == "travel":
        return "Anchor this travel-admin check to the next drill and verify the suspense before people disperse."
    if check.category == "readiness":
        return "Keep this as a standing pre-drill readiness standard, not a last-minute scramble."
    if check.category == "training":
        return (
            "Tie this recurring training check to the next event and record what standard or requirement it supports."
        )
    if check.category == "medical":
        return "Verify this recurring medical/readiness requirement against current local status before relying on it."
    return (
        "Keep this recurring check visible and attach it to a real cadence instead of letting it live as a vague "
        "note."
    )
