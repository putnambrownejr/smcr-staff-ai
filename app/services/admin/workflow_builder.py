from __future__ import annotations

from app.core.security import DEFAULT_WARNINGS
from app.schemas.admin_workflows import AdminWorkflowRequest, AdminWorkflowResponse, AdminWorkflowType


class AdminWorkflowBuilder:
    def build(self, request: AdminWorkflowRequest) -> AdminWorkflowResponse:
        checklist, required_documents, review_points = _workflow_parts(request.workflow_type)
        checklist = [*checklist, *[f"Fact to verify: {fact}" for fact in request.facts]]
        review_points = [
            *review_points,
            *[f"Constraint to respect: {constraint}" for constraint in request.constraints],
        ]
        return AdminWorkflowResponse(
            workflow_type=request.workflow_type,
            title=f"{request.workflow_type.value.replace('_', ' ').title()} workflow: {request.title}",
            checklist=checklist,
            required_documents=required_documents,
            review_points=review_points,
            warnings=[
                *DEFAULT_WARNINGS,
                "Admin workflow support is advisory only and must be reviewed by the appropriate admin chain.",
            ],
        )


def _workflow_parts(workflow_type: AdminWorkflowType) -> tuple[list[str], list[str], list[str]]:
    if workflow_type == AdminWorkflowType.dts_authorization:
        return (
            [
                "Confirm the mission purpose, travel dates, and expected funding path.",
                "Check whether the traveler has current orders or requires updated supporting documentation.",
                "Validate lodging, transportation, and estimated reimbursable expenses before submission.",
                "Identify approval chain timing early enough to avoid last-minute travel issues.",
            ],
            ["DTS authorization draft", "orders or travel directive", "cost estimate", "itinerary"],
            [
                "Verify official travel policy and local command routing before submission.",
                "Confirm the traveler understands what receipts and follow-up items will be needed later.",
            ],
        )
    if workflow_type == AdminWorkflowType.dts_voucher:
        return (
            [
                "Confirm travel dates, itinerary, and authorization status.",
                "Collect required receipts and validate local retention before upload.",
                "Verify the approving chain and suspense for voucher submission.",
                "Check for follow-up items after submission.",
            ],
            ["DTS reference", "travel receipts", "orders", "supporting itinerary"],
            ["Verify claimant data and amounts against official systems.", "Route through the appropriate approver."],
        )
    if workflow_type == AdminWorkflowType.gtcc:
        return (
            [
                "Identify the GTCC issue type: activation, declined charge, split disbursement, "
                "delinquency risk, or reconciliation.",
                "Confirm the related travel authorization, voucher status, and known suspense dates.",
                "Separate what the cardholder can do directly from what requires APC, S-1, or command follow-up.",
                "Capture follow-up owners before the issue goes stale between drills.",
            ],
            ["GTCC statement or issue summary", "related DTS authorization or voucher reference", "orders if relevant"],
            [
                "Verify current travel-card policy and local APC process before taking action.",
                "Do not place full card numbers or sensitive account details into local advisory notes.",
            ],
        )
    if workflow_type == AdminWorkflowType.orders_review:
        return (
            [
                "Check dates, reporting instructions, and duty status references.",
                "Confirm travel, lodging, and admin support implications.",
                "Identify required supporting documents and suspense items.",
            ],
            ["orders", "RQS/BIO as needed", "travel support note"],
            ["Verify the order version is current.", "Confirm final review through the proper command/admin chain."],
        )
    if workflow_type == AdminWorkflowType.award_package:
        return (
            [
                "Identify the award recommendation purpose and level.",
                "Gather supporting bullets, dates, and endorsement chain inputs.",
                "Check suspense and routing format requirements.",
            ],
            ["draft citation", "supporting bullets", "routing note"],
            ["Verify award criteria and local format requirements.", "Ensure human review before routing."],
        )
    return (
        [
            "Define the package purpose and suspense.",
            "List required enclosures and supporting references.",
            "Confirm routing sequence and final approval authority.",
        ],
        ["correspondence draft", "supporting references", "orders or admin support notes"],
        ["Verify format against current correspondence guidance.", "Ensure the package is complete before routing."],
    )
