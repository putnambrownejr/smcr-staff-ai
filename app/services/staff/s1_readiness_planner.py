from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import S1ReadinessRequest, S1ReadinessResponse


class S1ReadinessPlanner:
    def build(self, request: S1ReadinessRequest) -> S1ReadinessResponse:
        readiness_estimate = [
            f"Supported event: {request.supported_event}",
            "Identify what admin action changes execution reality versus what can remain a continuity note.",
            "Admin drift usually shows up as stale rosters, routing ambiguity, or travel suspense confusion.",
            "Keep one visible owner and suspense for each admin lane.",
        ]
        if request.audience:
            readiness_estimate.append(f"Supported audience / formation: {request.audience}")
        readiness_estimate.extend(f"Admin priority: {item}" for item in request.admin_priorities[:5])

        admin_status_board = [
            "Roster/accountability status: who is confirmed, pending, or unclear.",
            "Orders/routing status: what package is drafted, routed, approved, or blocked.",
            "Travel/admin status: what authorization, voucher, or GTCC issue still affects execution.",
            "Records/readiness status: what report, tracker, or continuity file needs refresh before next drill.",
        ]
        admin_status_board.extend(f"Admin risk to track: {item}" for item in request.admin_risks[:4])

        admin_task_tracker = [
            "Task tracker standard: one owner, one suspense, one status, and one command touchpoint per line.",
            "Task tracker lane: rosters, orders, DTS/GTCC, accountability, and records should not blur together.",
            (
                "Task tracker lane: separate this-drill must-finish items from continuity items "
                "that survive to the next cycle."
            ),
        ]
        admin_task_tracker.extend(f"Named admin task to track: {item}" for item in request.admin_priorities[:5])

        routing_matrix = [
            "Name the source reference, routing chain, reviewer, and suspense for each formal package.",
            "Separate internal staff coordination from command signature routing.",
            "Do not let travel, awards, fitness reports, and event admin contaminate one another's suspense lines.",
        ]
        if request.travel_required:
            routing_matrix.append(
                "Travel is in scope; confirm who owns DTS/GTCC friction and when it gets command visibility."
            )

        continuity_notes = [
            "Write turnover notes like the next drill will start cold.",
            "Refresh stale rosters, contact points, and package status before closeout.",
            "Capture unresolved admin facts in a form that survives reserve turnover and time gaps.",
        ]

        pre_drill_admin_readiness_check = [
            (
                "Pre-drill check: roster, accountability, and contact data are current enough "
                "to execute without a scramble."
            ),
            (
                "Pre-drill check: orders, routing packages, and signature requirements are "
                "where the staff thinks they are."
            ),
            "Pre-drill check: DTS, voucher, or GTCC friction has an owner and is visible before Marines disperse.",
            "Pre-drill check: unresolved admin friction is written down with a suspense, not remembered hopefully.",
        ]
        if request.travel_required:
            pre_drill_admin_readiness_check.append(
                "Pre-drill check: travel claims, receipts, authorizations, and GTCC issues are staged before execution."
            )

        critical_suspenses = [
            "What must be complete before the next drill begins?",
            "What must be routed before command review?",
            "What admin issue will hijack the event if ignored until execution week?",
        ]
        critical_suspenses.extend(f"Constraint to manage: {item}" for item in request.constraints[:3])

        return S1ReadinessResponse(
            title=f"S-1 readiness support: {request.title}",
            readiness_estimate=readiness_estimate,
            admin_status_board=admin_status_board,
            admin_task_tracker=admin_task_tracker,
            routing_matrix=routing_matrix,
            pre_drill_admin_readiness_check=pre_drill_admin_readiness_check,
            continuity_notes=continuity_notes,
            critical_suspenses=critical_suspenses,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "S-1 readiness support is advisory only and must be reconciled with current command admin "
                    "guidance, routing requirements, and verified roster/travel data."
                ),
            ],
        )
