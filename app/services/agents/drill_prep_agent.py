from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    DRILL_PREP_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class DrillPrepCalendarAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="drill-prep-calendar",
            name="Drill Prep Calendar Agent",
            description="Creates advisory drill-prep timelines, reminder lanes, and pre-drill task prompts.",
            domain="reserve administration",
            intended_users=["SMCR officers", "company staff", "battalion staff"],
            allowed_sources=["local calendar data", "stored handoff rhythm", "public training requirements"],
            disallowed_inputs=["calendar tokens", "PII not required for planning", "sensitive personal data"],
            system_prompt=(
                "Turn drill dates into practical advisory preparation timelines. Emphasize recurring checks, "
                "travel-admin friction, and what needs to happen before Marines walk in the door.\n\n"
                "Admin system awareness:\n"
                "- Drill Manager: captures IDT attendance → drives pay. Errors delay the entire pay cycle.\n"
                "- MROWS: generates ADT/AT orders. Must be submitted with enough lead time for approval.\n"
                "- DTS: travel vouchers. Post-drill voucher completion is the most common drop.\n"
                "- MOL: self-service for LES, OMPF, training records. Marines should verify before drill.\n"
                "- MCTFS/Unit Diary: authoritative system of record for all status changes.\n"
                "- MRRS/RHRP/PHA: medical readiness tracking — dental, PHA, IMR must be current.\n\n"
                "Key policy baselines:\n"
                "- 48 IDT + 14 days AT per year (MCO 1001R.1L w/CH-2, 7 Mar 2025).\n"
                "- MARADMIN 157/25: $750 IDT travel reimbursement cap.\n"
                "- AT planning triggers: T-45 (MROWS submission), T-30 (DTS authorization), T-15 (final coordination).\n\n"
                "Reserve friction points to front-load:\n"
                "- Asynchronous admin between drills (things break during the 28-day gap).\n"
                "- Dual-status civilians with employer notification requirements.\n"
                "- Geographic dispersion — Marines traveling from multiple states.\n"
                "- System fragmentation across 6+ platforms with different access requirements.\n"
                "- Compressed training year — 48 IDT periods to accomplish a full training plan."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Drill-prep calendar advisory draft.\n\n"
            "Use this to shape drill preparation rhythm, not as an official calendar authority.\n\n"
            "Primary drill-prep lenses:\n"
            "- What must be handled before drill, during drill, and immediately after release?\n"
            "- Which recurring checks should happen every cycle instead of being rediscovered each month?\n"
            "- What travel-admin, uniform, medical, or training friction should be front-loaded?\n\n"
            "My read:\n"
            "- Drill weekends fall apart when recurring checks live only in somebody's memory.\n"
            "- The best reminder plans are boring, repeatable, and tied to real due dates.\n"
            "- If post-drill cleanup is ignored, next month's prep starts already behind.\n\n"
            "Pre-drill (T-14 to T-1):\n"
            "- Confirm drill date, travel requirements, and must-hit suspense items.\n"
            "- Verify MOL access, LES accuracy, and medical readiness (dental, PHA, IMR).\n"
            "- Check DTS: prior voucher settled? New authorization needed?\n"
            "- Uniform, gear, and required annual training (MarineNet) complete.\n"
            "- MROWS: any ADT/AT orders pending approval?\n\n"
            "During drill:\n"
            "- Drill Manager attendance captured accurately (drives pay).\n"
            "- Capture action items while the right people are present.\n"
            "- FitRep counseling, awards routing, admin corrections — do it now or it waits 28 days.\n\n"
            "Post-drill (release + 5 days):\n"
            "- DTS voucher completion (most common drop).\n"
            "- Handoff notes updated for continuity between drills.\n"
            "- Unresolved admin items tracked with owners and deadlines.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(DRILL_PREP_REFERENCES),
            structured_citations=structured_citations(DRILL_PREP_REFERENCES),
            source_trust=source_trust_markers(
                DRILL_PREP_REFERENCES,
                notes_prefix=(
                    "Verify local drill dates, command rhythm, and current travel-admin guidance "
                    "before execution."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What is the next drill date and what must be true by first formation?",
                "Which recurring checks should become standing reminders?",
                "What post-drill cleanup item is most likely to be forgotten if we do not schedule it now?",
            ],
        )


def build_drill_prep_agent() -> DrillPrepCalendarAgent:
    return DrillPrepCalendarAgent()
