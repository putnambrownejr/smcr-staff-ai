from app.core.security import DEFAULT_WARNINGS
from app.schemas.training import (
    AnnualTrainingPlanRequest,
    AnnualTrainingPlanResponse,
    RangePackageRequest,
    RangePackageResponse,
)


class AnnualTrainingPlanner:
    def build(self, request: AnnualTrainingPlanRequest) -> AnnualTrainingPlanResponse:
        planning_phases = [
            "Define the training purpose, desired end state, and which events must happen at AT versus before AT.",
            "Back-plan transportation, lodging, funding, roster accountability, and required support requests.",
            "Rehearse reporting instructions, leader responsibilities, and post-event recovery/admin actions.",
        ]
        if request.date_window:
            planning_phases.append(f"Date window to validate: {request.date_window}")
        planning_phases.extend(f"Objective to cover: {item}" for item in request.training_objectives)

        admin_due_outs = [
            "Confirm orders status, roster/accountability, and attendance assumptions.",
            "Track medical/dental readiness references, annual requirements, and any waiver dependencies.",
            "Verify DTS, travel claims, lodging coordination, and receipt-retention plan if travel applies.",
            "Capture suspense dates for convoy/travel, training support, and required command approvals.",
        ]
        if request.constraints:
            admin_due_outs.extend(f"Constraint to plan around: {item}" for item in request.constraints)

        logistics_considerations = [
            "Transportation, billeting, chow, comm support, and equipment issue/turn-in.",
            "Ammo, range, facility, and training-area support if live-fire or field events are involved.",
            "Sustainment for reserve personnel arriving from distributed locations.",
        ]
        if request.travel_required:
            logistics_considerations.append(
                "Travel is in scope; validate arrival windows, rental/POV assumptions, "
                "and recovery timing."
            )
        if request.distributed_personnel:
            logistics_considerations.append(
                "Distributed personnel likely need earlier accountability and comm "
                "checks than a local-only event."
            )

        readiness_checks = [
            "Medical/dental readiness and annual admin requirements.",
            "Required licenses, certifications, or training currency tied to the event.",
            "Uniform, gear, and equipment serviceability checks before movement.",
            "Leader continuity plan for personnel changes between drills and AT execution.",
        ]

        coordination_points = [
            "Coordinate with S-3 / operations for event design and support synchronization.",
            "Coordinate with S-1 / admin for orders, roster, and travel/admin continuity.",
            "Coordinate with logistics and medical support early enough to adjust the plan before final lock-in.",
            "Pause for commander/OIC review before treating the AT plan as final.",
        ]
        if request.audience:
            coordination_points.append(f"Primary audience / participating population: {request.audience}")

        return AnnualTrainingPlanResponse(
            title=f"Annual training planning support: {request.unit_name}",
            planning_phases=planning_phases,
            admin_due_outs=admin_due_outs,
            logistics_considerations=logistics_considerations,
            readiness_checks=readiness_checks,
            coordination_points=coordination_points,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "AT planning support is advisory only and must be reconciled with "
                    "current orders, funding, and command guidance."
                ),
            ],
        )


class RangePackagePlanner:
    def build(self, request: RangePackageRequest) -> RangePackageResponse:
        packet_components = [
            "Range request / confirmation record",
            "Roster and accountability plan",
            "Weapons/ammo support plan",
            "Medical support and emergency-action reference",
            "Risk-management worksheet and control summary",
        ]
        if request.travel_required:
            packet_components.append("Travel and reporting instructions for distributed personnel")
        if request.overnight:
            packet_components.append("Billeting, chow, and overnight accountability plan")

        roles_and_responsibilities = [
            "OIC: overall event control and command review.",
            "RSO: firing-line safety, cease-fire authority, and enforcement of local SOP.",
            "Medical support: casualty response readiness and evacuation coordination.",
            "Ammo / logistics support: issue, turn-in, transport, and accountability.",
        ]
        if request.unit_name:
            roles_and_responsibilities.append(f"Unit context to confirm: {request.unit_name}")

        safety_controls = [
            "Confirm surface danger zone, firing sequence, and local range-specific controls with qualified personnel.",
            "Rehearse cease-fire, misfire, weapons condition, and movement procedures.",
            "Validate weather, heat/cold, hydration, and visibility controls.",
            "Assign supervision for ammo handling, weapons clearing, and accountability transitions.",
        ]

        medevac_and_comm_checks = [
            "Confirm who calls cease-fire and who initiates medical response.",
            "Verify casualty routing, pickup point, and supporting medical contact path.",
            "Check primary/alternate comm methods for range control, OIC, RSO, and medical support.",
            "Keep comm checks generic; do not store real frequencies or sensitive comm details in this prototype.",
        ]

        follow_up_requirements = [
            "Capture ammo turn-in, accountability closeout, and any incident/near-miss documentation.",
            "Record sustain/improve items with owners and suspense dates.",
            "Preserve only minimum local notes needed for continuity between drills.",
        ]
        if request.range_type:
            follow_up_requirements.append(f"Range type to validate with local SOP: {request.range_type}")
        if request.weapon_systems:
            follow_up_requirements.append("Weapon systems in scope: " + ", ".join(request.weapon_systems))
        if request.ammunition:
            follow_up_requirements.append("Ammunition in scope: " + ", ".join(request.ammunition))

        return RangePackageResponse(
            title=f"Range package support: {request.event_name}",
            packet_components=packet_components,
            roles_and_responsibilities=roles_and_responsibilities,
            safety_controls=safety_controls,
            medevac_and_comm_checks=medevac_and_comm_checks,
            follow_up_requirements=follow_up_requirements,
            warnings=[
                *DEFAULT_WARNINGS,
                "Range package support is advisory only and does not replace qualified RSO/OIC review or local SOP.",
            ],
        )
