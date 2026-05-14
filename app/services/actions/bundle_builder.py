from __future__ import annotations

from app.schemas.actions import ActionCategory, ActionItemRequest
from app.schemas.admin import AdminReadinessResponse
from app.schemas.chief import ChiefBriefResponse
from app.schemas.training import AnnualTrainingPlanResponse


class ActionBundleBuilder:
    def from_chief_brief(self, brief: ChiefBriefResponse) -> list[ActionItemRequest]:
        return [
            ActionItemRequest(
                user_key=brief.user_key,
                title=item.title,
                description=item.recommendation,
                category=_chief_category(item.category),
                priority=item.priority,
                suspense_date=item.due_date,
                source_ref=item.source,
                notes="Promoted from Chief/Aide brief.",
            )
            for item in brief.action_items
        ]

    def from_admin_readiness(self, readiness: AdminReadinessResponse) -> list[ActionItemRequest]:
        return [
            ActionItemRequest(
                user_key=readiness.user_key,
                title=item.title,
                description=item.recommendation,
                category=_admin_category(item.category),
                priority=item.priority,
                suspense_date=item.due_date,
                source_ref=item.source,
                notes="Promoted from admin readiness view.",
            )
            for item in readiness.items
        ]

    def from_annual_training_plan(
        self,
        response: AnnualTrainingPlanResponse,
        *,
        user_key: str | None,
        owner: str | None,
    ) -> list[ActionItemRequest]:
        items: list[ActionItemRequest] = []
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=f"AT phase: {line}",
                description="Annual training planning phase to confirm and sequence.",
                owner=owner,
                category=ActionCategory.training,
                priority="medium",
                source_ref=response.title,
                notes="Promoted from annual training planner.",
            )
            for line in response.planning_phases[:5]
        )
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=line,
                description="Admin due-out identified by annual training planner.",
                owner=owner,
                category=_training_category(line),
                priority=_line_priority(line),
                source_ref=response.title,
                notes="Promoted from annual training planner.",
            )
            for line in response.admin_due_outs[:8]
        )
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=line,
                description="Readiness check identified by annual training planner.",
                owner=owner,
                category=ActionCategory.readiness,
                priority="medium",
                source_ref=response.title,
                notes="Promoted from annual training planner.",
            )
            for line in response.readiness_checks[:6]
        )
        return items


def _chief_category(category: str) -> ActionCategory:
    mapping = {
        "documents": ActionCategory.documents,
        "drill": ActionCategory.drill,
        "career": ActionCategory.career,
        "fitrep": ActionCategory.fitrep,
        "pme": ActionCategory.pme,
        "admin": ActionCategory.admin,
        "readiness": ActionCategory.readiness,
        "handoff": ActionCategory.admin,
        "source_updates": ActionCategory.documents,
    }
    return mapping.get(category, ActionCategory.poam)


def _admin_category(category: str) -> ActionCategory:
    mapping = {
        "fitrep": ActionCategory.fitrep,
        "admin": ActionCategory.admin,
        "documents": ActionCategory.documents,
        "travel": ActionCategory.travel,
        "readiness": ActionCategory.readiness,
        "handoff": ActionCategory.admin,
    }
    return mapping.get(category, ActionCategory.poam)


def _training_category(line: str) -> ActionCategory:
    lowered = line.lower()
    if any(token in lowered for token in ("dts", "travel", "lodging", "receipt")):
        return ActionCategory.travel
    if any(token in lowered for token in ("medical", "dental", "readiness")):
        return ActionCategory.readiness
    if any(token in lowered for token in ("orders", "roster", "approval", "admin")):
        return ActionCategory.admin
    return ActionCategory.training


def _line_priority(line: str) -> str:
    lowered = line.lower()
    if any(token in lowered for token in ("confirm", "track", "verify", "approval", "orders")):
        return "high"
    if any(token in lowered for token in ("readiness", "travel", "dts")):
        return "medium"
    return "low"
