from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import SafetyPlanningRequest, SafetyPlanningResponse


class SafetyPlanner:
    def build(self, request: SafetyPlanningRequest) -> SafetyPlanningResponse:
        orm_framework = [
            f"Supported event: {request.supported_event}",
            "Frame hazards, controls, residual risk, and stop-training authority in plain language.",
            "Treat ORM as a commander decision tool, not an after-the-fact signature block.",
            "Verify which control measure is actually rehearsed and executable under friction.",
        ]
        if request.audience:
            orm_framework.append(f"Supported audience / formation: {request.audience}")
        orm_framework.extend(f"Hazard to evaluate: {item}" for item in request.hazards[:5])
        orm_framework.extend(f"Control to verify: {item}" for item in request.controls[:5])

        no_go_criteria = [
            "Stop when the unit cannot maintain positive control, communications, accountability, or medical response.",
            "Stop when the control measure exists on paper but not in trained execution.",
            "Stop when environmental or support conditions exceed what the commander accepted.",
        ]
        if request.live_fire:
            no_go_criteria.append(
                "Live-fire is in scope; stop if range-control, weapons-status, or SDZ controls break."
            )
        if request.vehicle_ops:
            no_go_criteria.append(
                "Vehicle movement is in scope; stop if movement control, driver status, or route control is unclear."
            )
        if request.overnight:
            no_go_criteria.append(
                "Overnight operations are in scope; stop if rest, accountability, or med-support continuity degrades."
            )

        residual_risk_decisions = [
            "Name what risk can be accepted, by whom, and at what review point.",
            "Separate acceptable friction from event-canceling risk.",
            "Do not hide a command decision inside generic ORM language.",
        ]
        residual_risk_decisions.extend(f"Named risk decision: {item}" for item in request.risk_decisions[:4])

        rehearsal_checks = [
            "Rehearse emergency action and lost-comm or lost-accountability actions at least once before execution.",
            "Verify who can stop, pause, or modify training and how that instruction is passed.",
            "Check that controls still work when the tempo increases or the schedule slips.",
        ]

        stop_training_triggers = [
            "Positive control is lost.",
            "Medical response assumptions fail.",
            "Communications or reporting discipline breaks past the accepted threshold.",
            "A required safety control cannot be executed as briefed.",
        ]
        stop_training_triggers.extend(f"Constraint-derived trigger: {item}" for item in request.constraints[:3])

        return SafetyPlanningResponse(
            title=f"Safety/ORM planning support: {request.title}",
            orm_framework=orm_framework,
            no_go_criteria=no_go_criteria,
            residual_risk_decisions=residual_risk_decisions,
            rehearsal_checks=rehearsal_checks,
            stop_training_triggers=stop_training_triggers,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "Safety planning support is advisory only and must be reconciled with ORM requirements, "
                    "range/local SOP, and commander risk-acceptance authority."
                ),
            ],
        )
