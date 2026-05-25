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

        pace_matrix = [
            {
                "level": "Primary",
                "method": "Best authorized method for routine command-and-control reporting.",
                "use": "Normal reports, accountability updates, and commander/XO synchronization.",
                "failure_trigger": "Missed report window, unreachable key node, or degraded access.",
                "owner": "S-6 validates method with S-3 and each reporting element before execution.",
            },
            {
                "level": "Alternate",
                "method": "Second authorized method that reaches the same decision-makers.",
                "use": "Routine traffic when the primary path is unavailable or overloaded.",
                "failure_trigger": "Alternate method cannot reach the required audience inside the reporting window.",
                "owner": "S-6 and unit leaders confirm users know when to switch.",
            },
            {
                "level": "Contingency",
                "method": "Simpler fallback method for degraded reporting and accountability.",
                "use": "Minimum essential reports, commander's critical information, and emergency coordination.",
                "failure_trigger": "Contingency path cannot pass the minimum essential report.",
                "owner": "S-3 defines minimum report content; S-6 confirms supportability.",
            },
            {
                "level": "Emergency",
                "method": "Last-resort authorized method for safety, accountability, or urgent command notification.",
                "use": "Life, limb, accountability, force protection, or lost-communication recovery.",
                "failure_trigger": "Emergency method fails or no acknowledgement is received.",
                "owner": "Commander/XO sets escalation rule; S-6 validates the method is understood.",
            },
        ]

        radio_guard_chart = [
            {
                "period": "Pre-execution comm check",
                "net_or_group": "Generic training net or approved reporting group",
                "station": "All reporting elements",
                "guard_responsibility": (
                    "Confirm reach-back, user access, and fallback method before movement or execution."
                ),
                "report_required": (
                    "Ready / not ready, missing users, degraded equipment, and unresolved access issues."
                ),
            },
            {
                "period": "Execution window",
                "net_or_group": "Primary reporting path",
                "station": "Command post or designated control node",
                "guard_responsibility": (
                    "Maintain accountability, receive scheduled reports, and track missed-report triggers."
                ),
                "report_required": "Scheduled status, CCIR/PIR-relevant updates, support requests, and safety issues.",
            },
            {
                "period": "Degraded comms",
                "net_or_group": "Alternate or contingency reporting path",
                "station": "Designated alternate guard station",
                "guard_responsibility": "Acknowledge switch-over, simplify traffic, and report unresolved outages.",
                "report_required": "Who is affected, what reports can still pass, and when the next check occurs.",
            },
            {
                "period": "Closeout",
                "net_or_group": "Primary or recovered reporting path",
                "station": "Command post and element leaders",
                "guard_responsibility": "Confirm accountability, collect comm friction, and capture AAR inputs.",
                "report_required": "Final accountability, unresolved equipment/access issues, and next-action owners.",
            },
        ]

        comm_plan_outline = [
            "Purpose: what command-and-control effect the comm plan must support.",
            "Supported event and audience: who must communicate, who must decide, and who must be informed.",
            (
                "Information flow: reports, CCIR/PIR linkage, report windows, acknowledgement rules, "
                "and missed-report action."
            ),
            "PACE matrix: authorized methods only, with switch criteria and owners.",
            "Radio guard / monitoring chart: periods, responsible stations, reports required, and escalation triggers.",
            "Support plan: equipment issue, power, user access, permissions, rehearsals, and help-desk path.",
            "Risk controls: lost-comm action, degraded reporting, sensitive-detail exclusion, and AAR capture.",
        ]

        information_management_checks = [
            "Define the minimum essential report before choosing a tool or network.",
            "Name the audience for each report and remove duplicate reporting paths.",
            "Set acknowledgement and missed-report rules that leaders can execute under friction.",
            "Keep real frequencies, COMSEC, call signs, sensitive network details, and current operational plans out.",
            "Tie comm rehearsals to the S-3 timeline and S-4 equipment/power support.",
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
            pace_matrix=pace_matrix,
            radio_guard_chart=radio_guard_chart,
            comm_plan_outline=comm_plan_outline,
            information_management_checks=information_management_checks,
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
