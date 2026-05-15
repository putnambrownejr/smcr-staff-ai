from app.core.security import DEFAULT_WARNINGS
from app.schemas.training import S4PlanningRequest, S4PlanningResponse


class S4Planner:
    def build(self, request: S4PlanningRequest) -> S4PlanningResponse:
        support_estimate = [
            f"Supported event: {request.supported_event}",
            f"Support objective: {request.support_objective}",
            "Identify the support requirement that is most likely to fail first if not confirmed early.",
            "Separate mandatory support needs from desirable enhancements.",
            "Decide early what support shortfall cancels the event and what merely reduces scope.",
        ]
        if request.audience:
            support_estimate.append(f"Supported audience / formation: {request.audience}")

        critical_support_requirements = [
            "Transportation and reporting requirements",
            "Billeting, chow, and accountability support",
            "Equipment, supply, and maintenance support",
            "Medical and safety support dependencies",
            "Communications support coordination where required",
        ]
        critical_support_requirements.extend(
            f"Named support requirement: {item}" for item in request.support_requirements
        )
        critical_support_requirements.extend(f"Constraint to work around: {item}" for item in request.constraints)

        movement_and_billeting = [
            "Confirm who moves when, by what means, and under what reporting instructions.",
            "Validate billeting, chow, and overnight-accountability assumptions as early as possible.",
            "Check recovery timing and return-to-home-station assumptions before locking the plan.",
        ]
        if request.travel_required:
            movement_and_billeting.append(
                "Travel is in scope; confirm arrival windows, reimbursement assumptions, and local transport support."
            )
        if request.overnight:
            movement_and_billeting.append(
                "Overnight support is in scope; verify billeting control, chow plan, and accountability battle rhythm."
            )

        sustainment_checks = [
            "Check equipment availability, issue/turn-in, and maintenance status.",
            "Check supply, ammo, and consumable support assumptions.",
            "Check support lead times and approval requirements for anything not controlled locally.",
            "Check recovery timing, reset burden, and what support debt gets kicked into the next drill.",
            "Confirm who closes out support shortfalls and unresolved logistics actions after drill.",
        ]

        coordination_points = [
            "Coordinate with S-3 for event design, timing, and support priorities.",
            "Coordinate with S-1 for orders, roster, travel, and accountability impacts.",
            "Coordinate with S-6, medical, safety, and any external support providers as required.",
            "Pause for command review before treating the support plan as fixed.",
        ]

        reserve_friction_points = [
            "Distributed personnel create movement and reporting friction before the event even starts.",
            "Reserve drill timelines compress coordination and amplify late support requests.",
            "Equipment and maintenance visibility may be weaker between drills than during active execution.",
            "Support assumptions drift quickly if no one leaves drill owning the suspense list.",
        ]
        if request.distributed_personnel:
            reserve_friction_points.append(
                "Distributed personnel require earlier accountability, movement confirmation, and sustainment planning."
            )

        return S4PlanningResponse(
            title=f"S-4 logistics planning support: {request.title}",
            support_estimate=support_estimate,
            critical_support_requirements=critical_support_requirements,
            movement_and_billeting=movement_and_billeting,
            sustainment_checks=sustainment_checks,
            coordination_points=coordination_points,
            reserve_friction_points=reserve_friction_points,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "S-4 logistics planning support is advisory only and must be reconciled with "
                    "current command guidance and verified support availability."
                ),
            ],
        )
