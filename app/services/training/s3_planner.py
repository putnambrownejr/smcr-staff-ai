from app.core.security import DEFAULT_WARNINGS
from app.schemas.training import S3PlanningRequest, S3PlanningResponse


class S3Planner:
    def build(self, request: S3PlanningRequest) -> S3PlanningResponse:
        mission_analysis = [
            f"Mission / training goal: {request.mission_or_training_goal}",
            f"Event type to plan around: {request.event_type}",
            "Confirm the desired end state, supported commander decision, and what success looks like at close-out.",
            "Separate what must be decided now from what can remain a follow-on action between drills.",
            "Build the smallest event that still trains to a real standard and produces a usable output.",
        ]
        if request.audience:
            mission_analysis.append(f"Primary audience / formation: {request.audience}")
        if request.timeframe:
            mission_analysis.append(f"Planning timeframe / window: {request.timeframe}")

        critical_tasks = [
            "Confirm the minimum products and rehearsals needed before execution.",
            "Identify support requests or approvals that sit on the critical path.",
            "Assign owners for tasking, tracking, and after-action capture.",
            "Translate the concept into specific drill-period tasks instead of leaving it as intent only.",
            "Kill nice-to-have activity that burns time without increasing standards or assessment value.",
        ]
        critical_tasks.extend(f"Constraint to manage: {item}" for item in request.constraints)

        sections = request.coordinating_sections or ["S-1", "S-4", "S-6", "Safety / ORM"]
        coordination_matrix = [
            f"{section}: identify required support, suspense, and decision needed from this section."
            for section in sections
        ]
        coordination_matrix.append("Commander / XO: confirm review point before treating the plan as final.")

        battle_rhythm = [
            "Before next drill: gather assumptions, missing information, and support requirements.",
            "At the start of drill: publish the short planning focus, priorities, and suspense list.",
            "During drill: run synchronization checks with supporting sections and capture decisions in writing.",
            "End of drill: confirm follow-up actions, required products, and owner handoffs before dismissal.",
            "Between drills: track unresolved suspense items and prep the next decision brief.",
        ]

        command_decision_points = [
            "What must the commander approve, prioritize, defer, or cancel?",
            "What support shortfall would force a branch or modified plan?",
            "What risk, timeline, or readiness issue needs command visibility before execution?",
            "What should be cut now so the unit can execute the remaining plan cleanly?",
        ]

        required_outputs = [
            "Short mission analysis / planning note",
            "Task list with owners and suspense dates",
            "Required correspondence or routing products",
            "Simple execution matrix or synchronization board",
            "Training/event support checklist",
            "AAR capture plan and post-event follow-up list",
        ]

        reserve_friction_points = [
            "Limited drill periods compress planning, coordination, and decision time.",
            "Distributed personnel create accountability and comm friction between drills.",
            "Support sections may not all be present at the same time, so handoff discipline matters.",
            "Admin and travel due-outs can quietly displace real operational focus if not separated early.",
        ]

        return S3PlanningResponse(
            title=f"S-3 planning support: {request.title}",
            mission_analysis=mission_analysis,
            critical_tasks=critical_tasks,
            coordination_matrix=coordination_matrix,
            battle_rhythm=battle_rhythm,
            command_decision_points=command_decision_points,
            required_outputs=required_outputs,
            reserve_friction_points=reserve_friction_points,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "S-3 planning support is advisory only and must be reconciled "
                    "with current command guidance and verified sources."
                ),
            ],
        )
