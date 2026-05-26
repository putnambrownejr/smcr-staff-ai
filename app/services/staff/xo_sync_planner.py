from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import XoSyncRequest, XoSyncResponse


class XoSyncPlanner:
    def build(self, request: XoSyncRequest) -> XoSyncResponse:
        sections = request.coordinating_sections or ["S-1", "S-3", "S-4", "S-6", "Safety", "Medical"]
        command_sync_frame = [
            f"Supported event: {request.supported_event}",
            f"Command focus: {request.command_focus}",
            "Reduce separate staff views to one executable fight with named owners and review points.",
            "If a decision, due-out, or friction point is still verbal, it is still unstable.",
        ]
        if request.audience:
            command_sync_frame.append(f"Supported audience / formation: {request.audience}")

        synchronization_matrix = [
            f"{section}: confirm what this lane owes, when it is due, and what command review it requires."
            for section in sections
        ]
        synchronization_matrix.extend(f"Constraint to manage: {item}" for item in request.constraints[:3])

        decision_support_matrix = [
            "Commander decision: what must be approved, cut, deferred, or reprioritized now.",
            "XO decision support: what friction must be resolved before the package can be called executable.",
            "Staff decision support: what support shortfall, timing issue, or coordination gap still needs an owner.",
        ]
        decision_support_matrix.extend(f"Named decision to surface: {item}" for item in request.critical_decisions[:4])

        due_out_tracker = [
            "Track one owner, one suspense, and one command touchpoint for every critical due-out.",
            "Separate products due this drill from continuity items that can survive to the next cycle.",
        ]
        due_out_tracker.extend(f"Named due-out: {item}" for item in request.due_outs[:6])

        command_review_points = [
            "Initial command review: confirm scope, main effort, and cut list before staff overbuilds.",
            "Mid-cycle review: confirm supportability, reporting discipline, and unresolved branch conditions.",
            "Pre-execution review: confirm owners, suspenses, no-go criteria, and what gets briefed up.",
            "Closeout review: confirm unresolved due-outs and turnover notes before Marines leave drill.",
        ]

        friction_checks = [
            "Which staff assumption is still carrying the plan?",
            "What breaks first in execution instead of in theory?",
            "What can be cut now to protect a cleaner execution standard?",
            "What issue is late only because nobody wanted to assign it clearly?",
        ]

        return XoSyncResponse(
            title=f"XO synchronization support: {request.title}",
            command_sync_frame=command_sync_frame,
            synchronization_matrix=synchronization_matrix,
            decision_support_matrix=decision_support_matrix,
            due_out_tracker=due_out_tracker,
            command_review_points=command_review_points,
            friction_checks=friction_checks,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "XO synchronization support is advisory only and must be reconciled with commander guidance, "
                    "actual tasking, and current staff ownership."
                ),
            ],
        )
