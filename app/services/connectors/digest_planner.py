from __future__ import annotations

from datetime import UTC, date, datetime

from app.core.security import DEFAULT_WARNINGS
from app.schemas.chief import ChiefActionItem
from app.schemas.connector_digest import (
    ChiefConnectorDigestRequest,
    ChiefConnectorDigestResponse,
    ConnectorEventSummary,
    ConnectorMessageSummary,
    ConnectorReadPlan,
    TravelEmailCaseSummary,
)
from app.schemas.connectors import ConnectorProvider, ConnectorWriteAction
from app.schemas.session import UserSessionHandoff
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.connectors.travel_email_interpreter import action_items_from_travel_cases, build_travel_cases
from app.services.session.handoff_store import SessionHandoffStore


class ChiefConnectorDigestPlanner:
    def __init__(self, handoff_store: SessionHandoffStore, travel_case_store: TravelCaseStore | None = None) -> None:
        self.handoff_store = handoff_store
        self.travel_case_store = travel_case_store or TravelCaseStore()

    def build(self, request: ChiefConnectorDigestRequest) -> ChiefConnectorDigestResponse:
        handoff = self.handoff_store.get(request.user_key)
        travel_cases = build_travel_cases(request.email_messages)
        if travel_cases:
            self.travel_case_store.upsert_many(request.user_key, travel_cases)
        read_plans = [
            _build_read_plan(consent.provider, consent.enabled, consent.access_mode.value)
            for consent in request.consents
        ]
        action_items = _sort_actions(
            [
                *_calendar_actions(request.calendar_events),
                *_email_actions(request.email_messages),
                *action_items_from_travel_cases(travel_cases),
                *_handoff_actions(handoff),
            ]
        )
        return ChiefConnectorDigestResponse(
            title="Chief/Aide connector digest plan",
            user_key=request.user_key,
            summary_lines=_summary_lines(request, handoff, action_items, travel_cases),
            read_plans=read_plans,
            travel_cases=travel_cases,
            action_items=action_items,
            staged_write_actions=_staged_writes(request),
            warnings=[
                *DEFAULT_WARNINGS,
                "Connector digest planning is advisory only. No live mailbox or calendar read was performed.",
                (
                    "Summaries in this response depend entirely on user-provided consent state "
                    "and provided event/message metadata."
                ),
            ],
        )


def _build_read_plan(provider: ConnectorProvider, enabled: bool, access_mode: str) -> ConnectorReadPlan:
    if provider in {ConnectorProvider.google_calendar, ConnectorProvider.microsoft_graph_calendar}:
        reads = [
            "Upcoming drill, PME, travel, and suspense events within the user-approved window.",
            "Event titles, start/end times, locations, and notes needed for task triage.",
        ]
    else:
        reads = [
            "Recent user-approved messages related to admin, travel, PME, FitRep, and drill preparation.",
            "Subject lines, senders, timestamps, and lightweight action hints only.",
        ]
    return ConnectorReadPlan(
        provider=provider,
        enabled=enabled,
        access_mode=access_mode,
        what_would_be_read=reads,
        safeguards=[
            "Review-before-write remains required.",
            "Do not store mailbox bodies, full threads, tokens, or credentials in the repo.",
            "Minimize retained content to the task-management fields actually needed.",
        ],
    )


def _calendar_actions(events: list[ConnectorEventSummary]) -> list[ChiefActionItem]:
    items: list[ChiefActionItem] = []
    for event in events[:8]:
        items.append(
            ChiefActionItem(
                title=f"Calendar: {event.title}",
                category="calendar",
                priority=_priority(event.start_at.date()),
                due_date=event.start_at.date(),
                source=event.provider.value,
                recommendation="Confirm time, location, and linked due-outs before acting on this event.",
            )
        )
    return items


def _email_actions(messages: list[ConnectorMessageSummary]) -> list[ChiefActionItem]:
    items: list[ChiefActionItem] = []
    for message in messages[:8]:
        title = message.subject if len(message.subject) <= 80 else message.subject[:77] + "..."
        items.append(
            ChiefActionItem(
                title=f"Email: {title}",
                category="email",
                priority="medium",
                due_date=message.received_at.date(),
                source=message.provider.value,
                recommendation=message.action_hint
                or "Review message context and decide whether it creates a suspense.",
            )
        )
    return items


def _handoff_actions(handoff: UserSessionHandoff | None) -> list[ChiefActionItem]:
    if handoff is None:
        return [
            ChiefActionItem(
                title="Add session handoff before connector triage",
                category="handoff",
                priority="medium",
                recommendation=(
                    "Add PME, FitRep, admin, and preference context so connector "
                    "summaries can be prioritized better."
                ),
            )
        ]
    actions: list[ChiefActionItem] = []
    for item in handoff.admin_watch_items[:5]:
        actions.append(
            ChiefActionItem(
                title=f"Handoff: {item}",
                category="handoff",
                priority="medium",
                recommendation="Cross-check this watch item against calendar and email summaries.",
            )
        )
    return actions


def _staged_writes(request: ChiefConnectorDigestRequest) -> list[ConnectorWriteAction]:
    writes: list[ConnectorWriteAction] = []
    if request.calendar_events:
        writes.append(
            ConnectorWriteAction(
                provider=request.calendar_events[0].provider,
                user_key=request.user_key,
                action_type="create_follow_up_event",
                payload_summary="Stage a follow-up event or reminder after reviewing the digest.",
                confirmation_token="review-before-write",
            )
        )
    if request.email_messages:
        writes.append(
            ConnectorWriteAction(
                provider=request.email_messages[0].provider,
                user_key=request.user_key,
                action_type="draft_reply_or_follow_up",
                payload_summary="Stage a reply draft or follow-up reminder after reviewing the digest.",
                confirmation_token="review-before-write",
            )
        )
    return writes


def _summary_lines(
    request: ChiefConnectorDigestRequest,
    handoff: UserSessionHandoff | None,
    actions: list[ChiefActionItem],
    travel_cases: list[TravelEmailCaseSummary],
) -> list[str]:
    lines = [
        (
            f"{len(request.calendar_events)} calendar event(s) and "
            f"{len(request.email_messages)} email item(s) were provided for planning."
        )
    ]
    enabled = [consent.provider.value for consent in request.consents if consent.enabled]
    if enabled:
        lines.append("Enabled connector plans: " + ", ".join(enabled) + ".")
    else:
        lines.append("No connector is enabled yet; this is a consent-safe dry run.")
    if handoff is None:
        lines.append(
            "No stored handoff was found, so connector signals cannot yet be tailored "
            "to the user's full watch list."
        )
    if travel_cases:
        lines.append(
            f"{len(travel_cases)} travel-related email case(s) were interpreted "
            "for voucher, receipt, or rental follow-up."
        )
    high_priority = sum(1 for item in actions if item.priority == "high")
    if high_priority:
        lines.append(f"{high_priority} high-priority connector-driven item(s) should be reviewed first.")
    return lines


def _sort_actions(actions: list[ChiefActionItem]) -> list[ChiefActionItem]:
    priority_order = {"high": 0, "medium": 1, "low": 2}

    def sort_key(action: ChiefActionItem) -> tuple[int, date]:
        return (priority_order.get(action.priority, 3), action.due_date or date.max)

    return sorted(actions, key=sort_key)


def _priority(due_date: date | None) -> str:
    if due_date is None:
        return "medium"
    days = (due_date - datetime.now(UTC).date()).days
    if days < 0 or days <= 7:
        return "high"
    if days <= 30:
        return "medium"
    return "low"
