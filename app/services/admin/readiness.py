from __future__ import annotations

from datetime import UTC, date, datetime

from app.core.security import DEFAULT_WARNINGS
from app.schemas.admin import AdminReadinessItem, AdminReadinessResponse
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.session import FitrepReminder, UserSessionHandoff
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.session.handoff_store import SessionHandoffStore


class AdminReadinessService:
    def __init__(
        self,
        handoff_store: SessionHandoffStore,
        document_organizer: PersonalDocumentOrganizer,
    ) -> None:
        self.handoff_store = handoff_store
        self.document_organizer = document_organizer

    def build(self, user_key: str) -> AdminReadinessResponse:
        handoff = self.handoff_store.get(user_key)
        document_summary = self.document_organizer.list_documents()
        items = _sort_items(
            [
                *_fitrep_items(handoff),
                *_admin_watch_items(handoff),
                *_document_items(document_summary),
                *_readiness_items(document_summary),
                *_travel_items(document_summary),
            ]
        )
        return AdminReadinessResponse(
            title="Admin readiness",
            user_key=user_key,
            handoff=handoff,
            summary_lines=_summary_lines(handoff, document_summary, items),
            items=items,
            document_summary=document_summary,
            source_trust=_admin_source_trust(),
            warnings=[
                *DEFAULT_WARNINGS,
                "Admin readiness is advisory only and does not replace official unit administration processes.",
                "Use current official orders, MCRAMM/PES references, and command guidance before acting.",
            ],
        )


def _fitrep_items(handoff: UserSessionHandoff | None) -> list[AdminReadinessItem]:
    if handoff is None:
        return []
    return [_fitrep_item(item) for item in handoff.fitreps]


def _fitrep_item(fitrep: FitrepReminder) -> AdminReadinessItem:
    return AdminReadinessItem(
        title=f"FitRep due: {fitrep.occasion}",
        category="fitrep",
        priority=_priority(fitrep.due_date),
        due_date=fitrep.due_date,
        recommendation="Confirm reporting chain, suspense dates, and required accomplishments/bullets.",
        source="session_handoff",
        source_trust=[
            SourceTrustMarker(
                tracked_title="PES / FitRep references",
                status=VerifiedSourceStatus.needs_review,
                notes="Verify the current PES / FitRep source before relying on this reminder.",
            )
        ],
    )


def _admin_watch_items(handoff: UserSessionHandoff | None) -> list[AdminReadinessItem]:
    if handoff is None:
        return [
            AdminReadinessItem(
                title="Create session handoff for admin tracking",
                category="handoff",
                priority="medium",
                recommendation="Add admin watch items, FitRep reminders, and core local document references.",
            )
        ]
    return [
        AdminReadinessItem(
            title=item,
            category="admin",
            priority=_watch_priority(item),
            recommendation="Assign a next suspense, owner, and supporting reference if needed.",
            source="session_handoff",
        )
        for item in handoff.admin_watch_items[:8]
    ]


def _document_items(document_summary: PersonalDocumentSummary | None) -> list[AdminReadinessItem]:
    if document_summary is None:
        return []
    items: list[AdminReadinessItem] = []
    required = {
        "rqs": "Add RQS reference",
        "orders": "Add current orders reference",
        "fitrep": "Add FitRep support reference",
        "dts": "Add DTS support reference",
    }
    present = {record.document_type.value for record in document_summary.records}
    for document_type, title in required.items():
        if document_type not in present:
            items.append(
                AdminReadinessItem(
                    title=title,
                    category="documents",
                    priority="medium" if document_type in {"rqs", "orders"} else "low",
                    recommendation="Store a local reference to support admin readiness and continuity.",
                    source_trust=_document_source_trust(document_type),
                )
            )
    if document_summary.review_due_count:
        items.append(
            AdminReadinessItem(
                title="Review due admin support documents",
                category="documents",
                priority="medium",
                recommendation="Refresh stale admin references, receipts, and certificates before relying on them.",
            )
        )
    if document_summary.expired_count:
        items.append(
            AdminReadinessItem(
                title="Replace expired admin support documents",
                category="documents",
                priority="high",
                recommendation="Update expired references before using them for readiness or admin actions.",
            )
        )
    return items


def _readiness_items(document_summary: PersonalDocumentSummary | None) -> list[AdminReadinessItem]:
    if document_summary is None:
        return []
    present = {record.document_type.value for record in document_summary.records}
    items: list[AdminReadinessItem] = []
    if "medical_readiness" not in present:
        items.append(
            AdminReadinessItem(
                title="Confirm medical readiness reference",
                category="readiness",
                priority="medium",
                recommendation=(
                    "Store or verify a local medical readiness reference if needed "
                    "for drill or AT planning."
                ),
            )
        )
    if "dental_readiness" not in present:
        items.append(
            AdminReadinessItem(
                title="Confirm dental readiness reference",
                category="readiness",
                priority="low",
                recommendation=(
                    "Store or verify a local dental readiness reference if needed "
                    "for mobilization tracking."
                ),
            )
        )
    return items


def _travel_items(document_summary: PersonalDocumentSummary | None) -> list[AdminReadinessItem]:
    if document_summary is None:
        return []
    present = {record.document_type.value for record in document_summary.records}
    items: list[AdminReadinessItem] = []
    if "travel_receipt" not in present:
        items.append(
            AdminReadinessItem(
                title="Track travel receipts locally",
                category="travel",
                priority="low",
                recommendation=(
                    "Store receipts or references locally if DTS voucher support is needed "
                    "after drill or travel."
                ),
            )
        )
    if "dts" not in present:
        items.append(
            AdminReadinessItem(
                title="Track DTS support locally",
                category="travel",
                priority="medium",
                recommendation="Store a local DTS reference or note if travel claims or authorizations are active.",
            )
        )
    return items


def _summary_lines(
    handoff: UserSessionHandoff | None,
    document_summary: PersonalDocumentSummary | None,
    items: list[AdminReadinessItem],
) -> list[str]:
    lines: list[str] = []
    if handoff is None:
        lines.append("No session handoff is stored, so admin prioritization is running with limited context.")
    else:
        lines.append(
            f"{len(handoff.admin_watch_items)} admin watch item(s) and "
            f"{len(handoff.fitreps)} FitRep reminder(s) are in the handoff."
        )
    if document_summary is not None and document_summary.total_documents:
        lines.append(f"{document_summary.total_documents} local document reference(s) are available for admin support.")
    high_priority = sum(1 for item in items if item.priority == "high")
    if high_priority:
        lines.append(f"{high_priority} high-priority admin item(s) should be handled first.")
    return lines


def _sort_items(items: list[AdminReadinessItem]) -> list[AdminReadinessItem]:
    priority_order = {"high": 0, "medium": 1, "low": 2}

    def sort_key(item: AdminReadinessItem) -> tuple[int, date]:
        return (priority_order.get(item.priority, 3), item.due_date or date.max)

    return sorted(items, key=sort_key)


def _priority(due_date: date | None) -> str:
    if due_date is None:
        return "medium"
    days = (due_date - datetime.now(UTC).date()).days
    if days < 0 or days <= 14:
        return "high"
    if days <= 45:
        return "medium"
    return "low"


def _watch_priority(item: str) -> str:
    lowered = item.lower()
    if any(token in lowered for token in ("fitrep", "voucher", "orders", "medical", "deadline", "suspense")):
        return "high"
    if any(token in lowered for token in ("travel", "pay", "dts", "award")):
        return "medium"
    return "low"


def _admin_source_trust() -> list[SourceTrustMarker]:
    return [
        SourceTrustMarker(
            tracked_title="MCRAMM / Reserve administration references",
            status=VerifiedSourceStatus.needs_review,
            notes="Use current public reserve administration references before acting.",
        ),
        SourceTrustMarker(
            tracked_title="PES / FitRep references",
            status=VerifiedSourceStatus.needs_review,
            notes="Use the current verified PES / FitRep reference before finalizing admin products.",
        ),
        SourceTrustMarker(
            tracked_title="DON / USMC correspondence guidance",
            status=VerifiedSourceStatus.needs_review,
            notes="Check current correspondence-formatting guidance before routing official packages.",
        ),
    ]


def _document_source_trust(document_type: str) -> list[SourceTrustMarker]:
    if document_type == "orders":
        return [
            SourceTrustMarker(
                tracked_title="Current orders reference",
                status=VerifiedSourceStatus.needs_review,
                notes="Confirm the local orders copy is current and complete before using it.",
            )
        ]
    if document_type == "fitrep":
        return [
            SourceTrustMarker(
                tracked_title="PES / FitRep references",
                status=VerifiedSourceStatus.needs_review,
                notes="Check current FitRep guidance before relying on stored support documents.",
            )
        ]
    return []
