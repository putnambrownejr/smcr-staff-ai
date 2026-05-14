from __future__ import annotations

from app.schemas.actions import ActionCategory, ActionItemRequest
from app.schemas.admin import AdminReadinessResponse
from app.schemas.chief import ChiefBriefResponse
from app.schemas.personnel import CorrespondenceConversionResponse
from app.schemas.poam import PoamResponse
from app.schemas.tdg import TdgGenerationResponse
from app.schemas.training import AnnualTrainingPlanResponse, RangePackageResponse


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

    def from_correspondence_conversion(
        self,
        response: CorrespondenceConversionResponse,
        *,
        user_key: str | None,
        owner: str | None,
    ) -> list[ActionItemRequest]:
        items: list[ActionItemRequest] = []
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=note,
                description="Routing or coordination note identified during correspondence conversion.",
                owner=owner,
                category=ActionCategory.admin,
                priority="medium",
                source_ref=response.title,
                notes="Promoted from correspondence conversion.",
            )
            for note in response.routing_notes[:6]
        )
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=point,
                description="Review point identified during correspondence conversion.",
                owner=owner,
                category=ActionCategory.documents,
                priority="medium",
                source_ref=response.title,
                notes="Promoted from correspondence conversion.",
            )
            for point in response.review_points[:6]
        )
        return items

    def from_range_package(
        self,
        response: RangePackageResponse,
        *,
        user_key: str | None,
        owner: str | None,
    ) -> list[ActionItemRequest]:
        items: list[ActionItemRequest] = []
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=item,
                description="Range packet component identified by range package support.",
                owner=owner,
                category=ActionCategory.training,
                priority="high",
                source_ref=response.title,
                notes="Promoted from range package planner.",
            )
            for item in response.packet_components[:6]
        )
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=item,
                description="Safety or comm check identified by range package support.",
                owner=owner,
                category=ActionCategory.readiness,
                priority="high",
                source_ref=response.title,
                notes="Promoted from range package planner.",
            )
            for item in [*response.safety_controls[:3], *response.medevac_and_comm_checks[:3]]
        )
        return items

    def from_tdg(
        self,
        response: TdgGenerationResponse,
        *,
        user_key: str | None,
        owner: str | None,
    ) -> list[ActionItemRequest]:
        items: list[ActionItemRequest] = []
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=item,
                description="Decision point identified by TDG generator.",
                owner=owner,
                category=ActionCategory.training,
                priority="medium",
                source_ref=response.title,
                notes="Promoted from TDG generator.",
            )
            for item in response.decision_points[:4]
        )
        items.extend(
            ActionItemRequest(
                user_key=user_key,
                title=item,
                description="Instructor follow-up note identified by TDG generator.",
                owner=owner,
                category=ActionCategory.pme,
                priority="low",
                source_ref=response.title,
                notes="Promoted from TDG generator.",
            )
            for item in response.instructor_notes[:4]
        )
        return items

    def from_poam(
        self,
        response: PoamResponse,
        *,
        user_key: str | None,
    ) -> list[ActionItemRequest]:
        return [
            ActionItemRequest(
                user_key=user_key,
                title=item.task,
                description=f"Workstream: {item.workstream}. Coordination: {', '.join(item.coordination)}.",
                owner=item.owner,
                category=ActionCategory.poam,
                priority="high",
                source_ref=response.title,
                notes=f"Suspense hint: {item.suspense_hint}",
            )
            for item in response.line_items[:24]
        ]


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
