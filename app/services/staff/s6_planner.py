from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import S6PlanRequest, S6PlanResponse


class S6Planner:
    def build(self, request: S6PlanRequest) -> S6PlanResponse:
        c2_support_estimate = [
            f"Supported event: {request.supported_event}",
            f"C2 objective: {request.c2_objective}",
            "Identify what communications support is essential for command and control versus simply convenient.",
            "Separate planning assumptions from any sensitive real-world technical detail.",
        ]
        if request.audience:
            c2_support_estimate.append(f"Supported audience / formation: {request.audience}")

        pace_considerations = [
            "Define primary, alternate, contingency, and emergency methods at a generic planning level.",
            "Check how comm degradation changes commander decisions, reporting flow, and accountability.",
            "Plan for local fallback methods if equipment, permissions, or support windows collapse.",
            "Reduce reporting methods and windows until Marines can actually execute them under friction.",
        ]

        support_requirements = [
            "Equipment availability and issue plan",
            "Battery/power and sustainment support",
            "Operator currency, licenses, or permissions",
            "Basic network/data support assumptions where applicable",
        ]
        support_requirements.extend(f"Named support requirement: {item}" for item in request.support_requirements)

        permissions_and_dependencies = [
            "Confirm what support requires prior coordination, access, approval, or external assistance.",
            "Check dependencies on S-3 timing, S-4 support, and local site constraints.",
            "Treat CAC, PKI, middleware, and portal-readiness problems as pre-drill issues, not same-day surprises.",
            "Keep COMSEC, real frequencies, and sensitive network details out of this prototype.",
        ]
        permissions_and_dependencies.extend(f"Constraint to manage: {item}" for item in request.constraints)

        reserve_friction_points = [
            "Distributed personnel can create comm check gaps before the event begins.",
            "Equipment access between drills may be limited or uneven.",
            "Licensing, permissions, and training currency can quietly become the critical path.",
            "Support windows may be too short to troubleshoot everything during drill.",
            "Too many reporting methods usually create confusion instead of redundancy.",
        ]
        if request.distributed_personnel:
            reserve_friction_points.append(
                "Distributed personnel require earlier comm checks and simpler fallback methods "
                "than a local-only event."
            )

        return S6PlanResponse(
            title=f"S-6 planning support: {request.title}",
            c2_support_estimate=c2_support_estimate,
            pace_considerations=pace_considerations,
            support_requirements=support_requirements,
            permissions_and_dependencies=permissions_and_dependencies,
            reserve_friction_points=reserve_friction_points,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "S-6 planning support is advisory only and must be reconciled with current guidance, "
                    "permissions, and authorized channels."
                ),
            ],
        )
