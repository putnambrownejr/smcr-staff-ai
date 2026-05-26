from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import SelExecutionRequest, SelExecutionResponse


class SelExecutionPlanner:
    def build(self, request: SelExecutionRequest) -> SelExecutionResponse:
        troop_flow_plan = [
            f"Supported event: {request.supported_event}",
            "Build troop flow around accountability, movement control, and sequence discipline.",
            "Keep transitions visible: show where Marines form, move, wait, report, and recover.",
            "Do not assume standards enforcement will appear by personality alone; write it into the flow.",
        ]
        if request.audience:
            troop_flow_plan.append(f"Supported audience / formation: {request.audience}")
        if request.formal_event:
            troop_flow_plan.append(
                "Formal-event discipline is in scope; sequence control, honors/protocol, and public-facing "
                "standards require rehearsal."
            )
        if request.overnight:
            troop_flow_plan.append(
                "Overnight accountability is in scope; define check points, leaders, and wake/sleep control."
            )

        accountability_scheme = [
            "Name how accountability is established, refreshed, and closed out.",
            "Define who owns accountability at each transition point.",
            "Tie missed-accountability action to the command and communications plan.",
        ]
        accountability_scheme.extend(
            f"Accountability risk to manage: {item}" for item in request.accountability_risks[:4]
        )

        troop_flow_checklist = [
            "Confirm first formation time, location, uniform, and release criteria before Marines arrive.",
            "Name who controls muster, movement release, holding areas, and final accountability closeout.",
            "Verify the troop flow sequence shows where Marines form, move, wait, report, and recover.",
            "Tie chow, transport, medical, and comm dependencies to the same troop flow "
            "instead of briefing them separately.",
        ]

        formation_transition_matrix = [
            "Opening formation: who forms the unit, verifies standards, and reports readiness upward.",
            "Movement transition: who releases, who receives, and how accountability is re-established on arrival.",
            "Execution transition: who controls the shift between phases, safety posture, and reporting rhythm.",
            "Dismissal transition: who confirms unresolved issues, release authority, and final accountability.",
        ]

        leader_touchpoints = [
            "Before movement or execution: leader confirmation of standards, accountability, and support posture.",
            "At each phase change: confirm headcount, support status, and any Marine issue requiring action.",
            "Before dismissal: confirm unresolved issues, turnover notes, and who owns the next follow-up.",
        ]
        leader_touchpoint_plan = [
            "Pre-event touchpoint: 1stSgt/SgtMaj confirms standards, troop flow, "
            "and accountability owners with the chain.",
            "Pre-movement touchpoint: leaders confirm headcount, transport posture, "
            "and any Marine issue requiring action.",
            "Mid-event touchpoint: leaders check welfare, discipline, and whether "
            "the schedule still matches Marine capacity.",
            "Pre-dismissal touchpoint: leaders resolve stragglers, unresolved "
            "welfare issues, and next-follow-up ownership.",
        ]

        standards_checks = [
            "Uniform and appearance standard is briefed and verified.",
            "Movement, formation, and reporting sequence are rehearsed if they matter to mission or ceremony success.",
            "Marines know what standard matters first, not just what rule exists in theory.",
        ]
        standards_checks.extend(f"Constraint to police: {item}" for item in request.constraints[:3])

        marine_welfare_checks = [
            "Check chow, hydration, rest, transport, and accountability assumptions before the schedule slips.",
            "Identify where a Marine issue becomes a command issue instead of an informal fix.",
            "Protect confidentiality and dignity while still giving command the readiness facts it needs.",
        ]

        return SelExecutionResponse(
            title=f"SEL execution support: {request.title}",
            troop_flow_plan=troop_flow_plan,
            troop_flow_checklist=troop_flow_checklist,
            accountability_scheme=accountability_scheme,
            formation_transition_matrix=formation_transition_matrix,
            leader_touchpoints=leader_touchpoints,
            leader_touchpoint_plan=leader_touchpoint_plan,
            standards_checks=standards_checks,
            marine_welfare_checks=marine_welfare_checks,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "SEL execution support is advisory only and must be reconciled with command standards, local "
                    "SOP, and current accountability requirements."
                ),
            ],
        )
