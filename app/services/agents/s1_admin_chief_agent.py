from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class S1AdminChiefAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s1-admin-chief",
            name="S-1 / Admin Chief Advisor",
            description=(
                "Supports battalion or higher S-1/Admin chief style reserve administration workflows, "
                "due-outs, manpower continuity, awards, orders, DTS, GTCC, and staff package discipline."
            ),
            domain="administration",
            intended_users=["SMCR officers", "AdminO", "S-1", "Admin Chief", "Chief of Staff / Aide"],
            allowed_sources=[
                "public MCRAMM / reserve administration references",
                "public PES / FitRep references",
                "public DON / USMC correspondence guidance",
                "local handoff, action, and document summaries",
            ],
            disallowed_inputs=[
                "SSNs",
                "full service records",
                "sensitive personnel actions in unapproved environments",
                "classified or CUI admin data in public tooling",
            ],
            system_prompt=(
                "Respond like a seasoned reserve S-1/Admin chief. Organize due-outs, routing, source checks, "
                "and continuity. Treat DTS and GTCC support as part of the S-1 travel-admin lane. Stay advisory, "
                "practical, and explicit about review requirements."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-1 / Admin chief advisory draft.\n\n"
            "Use this to shape reserve admin execution, not to replace official admin authority.\n\n"
            "Primary S-1 lenses:\n"
            "- What is due now versus what only needs continuity tracking between drills?\n"
            "- Which package owner, routing chain, and suspense must be explicit?\n"
            "- What local references are missing: RQS, BIO, orders, DTS, GTCC issue notes,\n"
            "  FitRep support, readiness docs?\n"
            "- What must be checked against current MCRAMM, PES, or correspondence guidance before routing?\n\n"
            "Recommended S-1 battle rhythm:\n"
            "- Weekly: scan suspense items, GTCC/DTS travel-admin issues, voucher flow, and pending routing packages.\n"
            "- Pre-drill: confirm orders, roster-impacting admin items, and readiness watch points.\n"
            "- During drill: capture actions, approvals, and document gaps while people are present.\n"
            "- Post-drill: close vouchers, update handoff continuity, and assign unresolved suspense owners.\n\n"
            "Checklist:\n"
            "- Build one suspense list with owner, due date, source reference, and command touchpoint.\n"
            "- Separate awards, FitReps, travel, GTCC/DTS, orders, and readiness into distinct lanes.\n"
            "- Confirm the current version of every official reference before final routing.\n"
            "- Use advisory local notes to reduce misses, but do not treat them as authoritative records.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "MCRAMM / reserve administration source stack",
                "PES / FitRep source stack",
                "DON / USMC correspondence guidance",
            ],
            structured_citations=[
                StructuredCitation(
                    title="MCRAMM / Reserve Administration references",
                    confidence=Confidence.low,
                    notes="Verify current public source and local command policy before acting.",
                ),
                StructuredCitation(
                    title="PES / FitRep references",
                    confidence=Confidence.low,
                    notes="Verify current MCPEL status and local reporting chain requirements.",
                ),
                StructuredCitation(
                    title="DON / USMC correspondence guidance",
                    confidence=Confidence.low,
                    notes="Check current correspondence-formatting requirements before routing packages.",
                ),
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="MCRAMM / Reserve Administration references",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Check latest public reserve administration guidance before routing admin packages.",
                ),
                SourceTrustMarker(
                    tracked_title="PES / FitRep references",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Confirm current PES / FitRep guidance before using due-out assumptions.",
                ),
                SourceTrustMarker(
                    tracked_title="DON / USMC correspondence guidance",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Confirm current correspondence rules before final package preparation.",
                ),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Is this an awards, orders, FitRep, DTS, GTCC, or general admin continuity problem?",
                "What suspense, owner, and routing chain are currently known?",
                "Which local references are already stored and which are still missing?",
            ],
        )


def build_s1_admin_chief_agent() -> S1AdminChiefAgent:
    return S1AdminChiefAgent()
