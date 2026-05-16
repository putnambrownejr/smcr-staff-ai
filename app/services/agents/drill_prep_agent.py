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
                "travel-admin friction, and what needs to happen before Marines walk in the door."
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
            "Checklist:\n"
            "- Confirm next drill date, travel requirements, and any must-hit suspense items.\n"
            "- Build pre-drill reminders for grooming, uniform, gear, medical, DTS/GTCC, and required training.\n"
            "- Capture in-drill action items while the right people are present.\n"
            "- Schedule post-drill cleanup for vouchers, unresolved admin, and handoff updates.\n"
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
