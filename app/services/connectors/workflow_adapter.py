from __future__ import annotations

from app.schemas.actions import (
    ActionCategory,
    ActionPriority,
    ActionPromoteItemRequest,
    ActionPromoteRequest,
)
from app.schemas.connector_digest import (
    ChiefConnectorDigestRequest,
    ChiefConnectorDigestResponse,
    ConnectorEventSummary,
    ConnectorMessageSummary,
    ConnectorWorkflowActionItem,
    ConnectorWorkflowAdapterRequest,
    ConnectorWorkflowAdapterResponse,
)
from app.schemas.handoff_updates import HandoffUpdateDraftRequest
from app.services.connectors.digest_planner import ChiefConnectorDigestPlanner


class ConnectorWorkflowAdapter:
    def __init__(self, planner: ChiefConnectorDigestPlanner) -> None:
        self.planner = planner

    def build(self, request: ConnectorWorkflowAdapterRequest) -> ConnectorWorkflowAdapterResponse:
        digest_request = ChiefConnectorDigestRequest(
            user_key=request.user_key,
            consents=request.consents,
            calendar_events=request.calendar_events,
            email_messages=request.email_messages,
        )
        digest = self.planner.build(digest_request)
        handoff_note_lines = [
            *_calendar_handoff_lines(request.calendar_events),
            *_email_handoff_lines(request.email_messages),
        ]
        action_items = _action_items_from_digest(digest)
        action_promote_request = ActionPromoteRequest(
            user_key=request.user_key,
            default_category=ActionCategory.admin,
            default_priority=ActionPriority.medium,
            source_ref="connector_adapter",
            items=[
                ActionPromoteItemRequest(
                    text=item.text,
                    category=item.category,
                    priority=item.priority,
                    source_ref=item.source_ref,
                    notes=item.notes,
                )
                for item in action_items
            ],
        )
        return ConnectorWorkflowAdapterResponse(
            title="Connector workflow adapter",
            user_key=request.user_key,
            summary_lines=[
                "Connector-fed summaries were normalized into Chief/Aide, handoff, and action-ready shapes.",
                "No live connector execution or local write was performed.",
                f"{len(action_items)} connector-driven action candidate(s) are ready for promotion if approved.",
            ],
            digest=digest,
            handoff_draft_request=HandoffUpdateDraftRequest(
                title="Connector-derived handoff update",
                notes="\n".join(handoff_note_lines) or "No connector-derived handoff notes were generated.",
            ),
            handoff_note_lines=handoff_note_lines,
            action_items=action_items,
            action_promote_request=action_promote_request,
            warnings=[
                *digest.warnings,
                "Use the handoff draft/apply flow before changing stored user context.",
                "Use action promotion only after confirming the connector-derived due-outs are real and relevant.",
            ],
        )


def _calendar_handoff_lines(events: list[ConnectorEventSummary]) -> list[str]:
    lines: list[str] = []
    for event in events[:6]:
        note = f"Admin watch: calendar event {event.title} on {event.start_at.date()}"
        if event.location:
            note += f" at {event.location}"
        lines.append(note)
        if event.notes:
            lines.append(f"Recurring drill note: {event.notes}")
    return lines


def _email_handoff_lines(messages: list[ConnectorMessageSummary]) -> list[str]:
    lines: list[str] = []
    for message in messages[:6]:
        if message.action_hint:
            lines.append(f"Admin watch: {message.subject} - {message.action_hint}")
        else:
            lines.append(f"Admin watch: review email subject {message.subject}")
    return lines


def _action_items_from_digest(digest: ChiefConnectorDigestResponse) -> list[ConnectorWorkflowActionItem]:
    items: list[ConnectorWorkflowActionItem] = []
    for action in digest.action_items[:10]:
        category = _map_category(action.category)
        priority = ActionPriority(action.priority)
        items.append(
            ConnectorWorkflowActionItem(
                text=action.title,
                category=category,
                priority=priority,
                source_ref=action.source,
                notes=action.recommendation,
            )
        )
    return items


def _map_category(category: str | None) -> ActionCategory:
    mapping = {
        "calendar": ActionCategory.drill,
        "email": ActionCategory.admin,
        "handoff": ActionCategory.admin,
        "fitrep": ActionCategory.fitrep,
        "pme": ActionCategory.pme,
        "career": ActionCategory.career,
        "documents": ActionCategory.documents,
        "drill": ActionCategory.drill,
        "travel": ActionCategory.travel,
        "admin": ActionCategory.admin,
        "source_updates": ActionCategory.documents,
    }
    return mapping.get(category or "", ActionCategory.other)
