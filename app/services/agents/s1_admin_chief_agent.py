from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S1_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


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
                "public DTS and GTCC training references",
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
                "practical, explicit about review requirements, and intolerant of vague suspense ownership. Sound "
                "like someone who has watched good packages die from weak routing discipline and stale continuity."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-1 / Admin chief advisory draft.\n\n"
            "Use this to shape reserve admin execution, not to replace official admin authority.\n\n"
            "Bottom line:\n"
            "- If the suspense, owner, routing chain, and required reference are not explicit,\n"
            "  then it is not under control yet.\n\n"
            "Primary S-1 lenses:\n"
            "- What is due now versus what only needs continuity tracking between drills?\n"
            "- Which package owner, routing chain, and suspense must be explicit?\n"
            "- What local references are missing: RQS, BIO, orders, DTS, GTCC issue notes,\n"
            "  FitRep support, readiness docs?\n"
            "- What must be checked against current MCRAMM, PES, or correspondence guidance before routing?\n\n"
            "My read:\n"
            "- Admin friction comes from drift, stale notes, and nobody owning the last 10 percent.\n"
            "- The plan is weak if it depends on finding the right document after everyone has gone home.\n"
            "- DTS and GTCC problems should be treated as continuity fights, not one-off emergencies.\n"
            "- Every routing package needs a last responsible adult. If that person is unclear,\n"
            "  the package is late already.\n\n"
            "Recommended S-1 battle rhythm:\n"
            "- Weekly: scan suspense items, GTCC/DTS travel-admin issues, voucher flow, and pending routing packages.\n"
            "- Pre-drill: confirm orders, roster-impacting admin items, and readiness watch points.\n"
            "- During drill: capture actions, approvals, and document gaps while people are present.\n"
            "- Post-drill: close vouchers, update handoff continuity, and assign unresolved suspense owners.\n\n"
            "Checklist:\n"
            "- Build one suspense list with owner, due date, source reference, and command touchpoint.\n"
            "- Separate awards, FitReps, travel, GTCC/DTS, orders, and readiness into distinct lanes.\n"
            "- Force a source check before routing anything that claims to be final.\n"
            "- Confirm the current version of every official reference before final routing.\n"
            "- Use advisory local notes to reduce misses, but do not treat them as authoritative records.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(S1_REFERENCES),
            structured_citations=structured_citations(S1_REFERENCES),
            source_trust=source_trust_markers(
                S1_REFERENCES,
                notes_prefix="Confirm current admin, correspondence, and travel process guidance before routing.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this an awards, orders, FitRep, DTS, GTCC, or general admin continuity problem?",
                "What suspense, owner, and routing chain are currently known?",
                "Which local references are already stored and which are still missing?",
            ],
        )


def build_s1_admin_chief_agent() -> S1AdminChiefAgent:
    return S1AdminChiefAgent()
