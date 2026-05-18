from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.core.security import DEFAULT_WARNINGS
from app.schemas.career import CareerWatchItem, CareerWatchResponse
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.reading_state import ReadingProgressRecord, ReadingProgressStatus
from app.schemas.session import UserSessionHandoff
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.reading.state_store import ReadingProgressStore
from app.services.session.handoff_store import SessionHandoffStore


class CareerWatchService:
    def __init__(
        self,
        handoff_store: SessionHandoffStore,
        document_organizer: PersonalDocumentOrganizer,
        opportunity_tracker: OpportunityTracker,
        reading_catalog: ReadingListCatalogService,
        reading_state_store: ReadingProgressStore | None = None,
    ) -> None:
        self.handoff_store = handoff_store
        self.document_organizer = document_organizer
        self.opportunity_tracker = opportunity_tracker
        self.reading_catalog = reading_catalog
        self.reading_state_store = reading_state_store or ReadingProgressStore("reading_state")

    def build_watch(self, user_key: str) -> CareerWatchResponse:
        handoff = self.handoff_store.get(user_key)
        document_summary = self.document_organizer.list_documents()
        tracked_opportunities = list(self.opportunity_tracker.list())[:5]
        reading_progress = self.reading_state_store.list(user_key).records
        watch_items = _sort_items(
            [
                *_pme_items(handoff),
                *_fitrep_items(handoff),
                *_document_items(document_summary, handoff),
                *_opportunity_items(tracked_opportunities),
                *_trend_items(handoff),
                *_course_items(handoff),
            ]
        )
        return CareerWatchResponse(
            title="Career watch",
            user_key=user_key,
            handoff=handoff,
            handoff_is_stale=_handoff_is_stale(handoff),
            watch_items=watch_items,
            tracked_opportunities=tracked_opportunities,
            document_summary=document_summary,
            recommended_books=_recommended_books(self.reading_catalog, handoff, reading_progress),
            recommended_courses=_recommended_courses(handoff),
            career_trends=handoff.career_trends if handoff is not None else [],
            warnings=_warnings(handoff),
        )


def _pme_items(handoff: UserSessionHandoff | None) -> list[CareerWatchItem]:
    if handoff is None:
        return [
            CareerWatchItem(
                title="Create session handoff for career tracking",
                category="handoff",
                priority="medium",
                recommendation="Add PME status, FitRep dates, billet, MOS, and career preferences.",
            )
        ]
    return [
        CareerWatchItem(
            title=f"PME watch: {item.program} is {item.status}",
            category="pme",
            priority=_priority(item.due_date),
            due_date=item.due_date,
            recommendation="Confirm the next milestone, enrollment status, and completion plan.",
            source="session_handoff",
        )
        for item in handoff.pme
    ]


def _fitrep_items(handoff: UserSessionHandoff | None) -> list[CareerWatchItem]:
    if handoff is None:
        return []
    return [
        CareerWatchItem(
            title=f"FitRep watch: {item.occasion}",
            category="fitrep",
            priority=_priority(item.due_date),
            due_date=item.due_date,
            recommendation="Confirm RS/RO timelines, input requirements, and draft suspense.",
            source="session_handoff",
        )
        for item in handoff.fitreps
    ]


def _document_items(
    document_summary: PersonalDocumentSummary | None,
    handoff: UserSessionHandoff | None,
) -> list[CareerWatchItem]:
    if document_summary is None:
        return []
    items: list[CareerWatchItem] = []
    for doc_type in document_summary.missing_recommended_types:
        title = {
            "rqs": "Add RQS reference",
            "bio": "Add BIO reference",
            "orders": "Add current orders reference",
            "pme_certificate": "Add PME certificate reference",
        }.get(doc_type, f"Add {doc_type} reference")
        items.append(
            CareerWatchItem(
                title=title,
                category="documents",
                priority="medium" if doc_type == "rqs" else "low",
                recommendation="Store a local reference so the app can support career and readiness tracking.",
            )
        )
    if document_summary.review_due_count:
        items.append(
            CareerWatchItem(
                title="Review due local career documents",
                category="documents",
                priority="medium",
                recommendation="Refresh stale references, certificates, or supporting documents.",
            )
        )
    if document_summary.expired_count:
        items.append(
            CareerWatchItem(
                title="Replace expired local career documents",
                category="documents",
                priority="high",
                recommendation="Update expired orders, readiness items, or certificates before relying on them.",
            )
        )
    if handoff is not None and handoff.bio_context_id is None and _has_document_type(document_summary, "bio"):
        items.append(
            CareerWatchItem(
                title="Link BIO in session handoff",
                category="handoff",
                priority="low",
                recommendation="Set bio_context_id so the career watch can reference it directly.",
            )
        )
    return items


def _opportunity_items(opportunities: list[OpportunityRecord]) -> list[CareerWatchItem]:
    return [
        CareerWatchItem(
            title=f"Opportunity watch: {opportunity.title}",
            category="opportunity",
            priority=_priority(opportunity.due_date),
            due_date=opportunity.due_date,
            recommendation="Review fit, verify eligibility, and decide whether to pursue or archive it.",
            source=opportunity.source_url,
        )
        for opportunity in opportunities
        if opportunity.tracked
    ]


def _trend_items(handoff: UserSessionHandoff | None) -> list[CareerWatchItem]:
    if handoff is None:
        return []
    return [
        CareerWatchItem(
            title=f"Trend watch: {trend.label}",
            category="career_trend",
            priority="medium",
            recommendation=trend.recommended_action or "Review this trend and decide on the next action.",
            source="session_handoff",
        )
        for trend in handoff.career_trends
    ]


def _course_items(handoff: UserSessionHandoff | None) -> list[CareerWatchItem]:
    if handoff is None:
        return []
    return [
        CareerWatchItem(
            title=f"Course watch: {course}",
            category="course",
            priority="low",
            recommendation="Decide whether to enroll, complete, or archive this course recommendation.",
            source="session_handoff",
        )
        for course in handoff.recommended_courses
    ]


def _recommended_books(
    catalog: ReadingListCatalogService,
    handoff: UserSessionHandoff | None,
    reading_progress: list[ReadingProgressRecord],
) -> list[str]:
    progress_by_slug = {record.slug: record for record in reading_progress}
    in_progress = [record for record in reading_progress if record.status == ReadingProgressStatus.in_progress]
    suggestions: list[str] = [f"Continue reading: {record.title}" for record in in_progress[:2]]
    preferred_category = None
    if handoff is not None and handoff.mos:
        if handoff.mos.startswith("06"):
            preferred_category = "communications"
        elif handoff.mos.startswith("05"):
            preferred_category = "planning"
        elif handoff.mos.startswith("18"):
            preferred_category = "leadership"
    books = catalog.list_books(category=preferred_category, open_source_only=True) if preferred_category else []
    if not books:
        books = catalog.list_books(open_source_only=True)
    for book in books:
        progress = progress_by_slug.get(book.slug)
        if progress is not None and progress.status == ReadingProgressStatus.completed:
            continue
        suggestions.append(book.title)
        if len(suggestions) >= 3:
            break
    return _dedupe(suggestions)[:3]


def _recommended_courses(handoff: UserSessionHandoff | None) -> list[str]:
    if handoff is None:
        return []
    ordered: list[str] = []
    if handoff.pme:
        for pme in handoff.pme:
            ordered.append(f"PME follow-up: {pme.program}")
    ordered.extend(handoff.recommended_courses)
    return _dedupe(ordered)[:5]


def _warnings(handoff: UserSessionHandoff | None) -> list[str]:
    warnings = list(DEFAULT_WARNINGS)
    warnings.extend(
        [
            "Career watch is advisory only and does not determine eligibility, command decisions, or board outcomes.",
            "Local career data should be kept to the minimum necessary and reviewed before any external sharing.",
        ]
    )
    if _handoff_is_stale(handoff):
        warnings.append("Session handoff appears stale. Refresh PME, FitRep, and career notes before relying on it.")
    return warnings


def _handoff_is_stale(handoff: UserSessionHandoff | None) -> bool:
    if handoff is None:
        return False
    return handoff.updated_at < datetime.now(UTC) - timedelta(days=30)


def _priority(due_date: date | None) -> str:
    if due_date is None:
        return "medium"
    days = (due_date - datetime.now(UTC).date()).days
    if days < 0 or days <= 14:
        return "high"
    if days <= 45:
        return "medium"
    return "low"


def _sort_items(items: list[CareerWatchItem]) -> list[CareerWatchItem]:
    priority_order = {"high": 0, "medium": 1, "low": 2}

    def sort_key(item: CareerWatchItem) -> tuple[int, date]:
        return (priority_order.get(item.priority, 3), item.due_date or date.max)

    return sorted(items, key=sort_key)


def _has_document_type(summary: PersonalDocumentSummary, document_type: str) -> bool:
    return any(record.document_type.value == document_type for record in summary.records)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
