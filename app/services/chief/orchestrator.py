from datetime import UTC, date, datetime, timedelta

from app.core.security import DEFAULT_WARNINGS
from app.schemas.calendar import DrillPrepPlanResponse
from app.schemas.chief import ChiefActionItem, ChiefBriefRequest, ChiefBriefResponse
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.session import FitrepReminder, PmeStatus, UserSessionHandoff
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.document_update_monitor import DocumentUpdateMonitor
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore


class ChiefAideOrchestrator:
    def __init__(
        self,
        handoff_store: SessionHandoffStore,
        document_organizer: PersonalDocumentOrganizer,
        drill_plan_store: DrillPrepPlanStore,
        reading_catalog: ReadingListCatalogService,
    ) -> None:
        self.handoff_store = handoff_store
        self.document_organizer = document_organizer
        self.drill_plan_store = drill_plan_store
        self.reading_catalog = reading_catalog

    def build_brief(self, request: ChiefBriefRequest) -> ChiefBriefResponse:
        handoff = self.handoff_store.get(request.user_key) if request.user_key else None
        handoff_is_stale = _handoff_is_stale(handoff)
        document_summary = self.document_organizer.list_documents() if request.include_personal_documents else None
        drill_plans = self.drill_plan_store.list() if request.include_drill_plans else []
        updates = DocumentUpdateMonitor().scan_maradmin_records(request.maradmin_records).candidates
        action_items = [
            *_handoff_actions(handoff),
            *_document_actions(document_summary, handoff),
            *_drill_actions(drill_plans),
            *_update_actions(updates),
        ]
        return ChiefBriefResponse(
            title="Chief of Staff / Aide de Camp triage brief",
            user_key=request.user_key,
            handoff=handoff,
            handoff_is_stale=handoff_is_stale,
            action_items=_sort_actions(action_items),
            document_summary=document_summary,
            drill_plans=drill_plans,
            documentation_updates=updates,
            reading_recommendations=_reading_recommendations(self.reading_catalog),
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


def _update_actions(updates: list[DocumentationUpdateCandidate]) -> list[ChiefActionItem]:
    return [
        ChiefActionItem(
            title=f"Possible source update: {update.tracked_title}",
            category="source_updates",
            priority="high" if update.confidence == "high" else "medium",
            source=update.trigger_url,
            recommendation="Verify the current official source before relying on stored summaries or citations.",
        )
        for update in updates
    ]


def _reading_recommendations(catalog: ReadingListCatalogService) -> list[str]:
    books = catalog.list_books(open_source_only=True)
    return [book.title for book in books[:3]]


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
