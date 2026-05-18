from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    INFANTRY_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class Infantry03xxAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="infantry-03xx-advisor",
            name="Infantry / 03XX Advisor",
            description=(
                "Supports the S-3 family with infantry-flavored training design, basic tactical framing, "
                "patrolling refreshers, urban familiarization, and leader rehearsal worksheets while refusing "
                "sensitive real-world operational details."
            ),
            domain="infantry and ground training",
            intended_users=["SMCR officers", "S-3", "company staff", "OICs", "platoon leaders", "trainers"],
            allowed_sources=[
                "public infantry doctrine",
                "public training and readiness references",
                "public TBS and SOI framing references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified operations",
                "real-world target packages",
                "sensitive force-protection details",
                "exact real-world movements",
                "unapproved detailed tactics for real operations",
            ],
            system_prompt=(
                "Respond like an infantry-savvy training advisor under a hard-driving S-3. Keep the tone blunt, "
                "practical, and standards-based. Distinguish familiarization from qualification, leader "
                "development from theatrics, and controlled training value from fake high-speed nonsense. Stay "
                "training-safe and advisory."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = "Active local operating context:\n" + "\n".join(
                f"- {line}" for line in active_context_lines
            ) + "\n\n"

        answer = (
            "Infantry / 03XX advisory draft under the S-3 family.\n\n"
            "Use this to shape infantry-flavored training, not to replace qualified 03xx leaders, local SOPs, "
            "or formal schoolhouse progression.\n\n"
            f"{active_context_block}"
            "Bottom line:\n"
            "- Keep the package honest.\n"
            "- If the Marines are not 03s, train fundamentals, control, and confidence before complexity.\n"
            "- If the leaders cannot brief, rehearse, supervise, and assess it cleanly, the lane is too big.\n\n"
            "Primary 03xx training lenses:\n"
            "- Is this familiarization, qualification, sustainment, or leader development?\n"
            "- What standard is being trained, and what level of mastery is realistic for this population?\n"
            "- What schoolhouse baseline should inform the event: TBS officer mindset, SOI teach-and-mentor model, "
            "or infantry T&R standard?\n"
            "- What must be dry-rehearsed before blanks, movement, or friction are added?\n"
            "- What should be cut now so the event trains fundamentals instead of ego?\n\n"
            "What this lane is good for:\n"
            "- infantry familiarization packages for non-03 Marines\n"
            "- patrolling refreshers with simple tactical vocabulary and leader checks\n"
            "- blank-fire urban lanes that emphasize control, sectors, reporting, and casualty actions\n"
            "- leader rehearsal and OIC worksheets before execution\n\n"
            "My read:\n"
            "- Good infantry-flavored training for support Marines is usually simpler than people want and more "
            "repetitive than people expect.\n"
            "- TBS and SOI both point the same direction: common warfighting language, leader control, repetition, "
            "and evaluation matter more than trying to look advanced.\n"
            "- If the lane starts looking cinematic, it is probably drifting away from useful training.\n\n"
            "Checklist:\n"
            "- Name the training population and be honest about its baseline.\n"
            "- Decide whether the event is building vocabulary, movement discipline, reporting, patrolling habits, "
            "or leader supervision.\n"
            "- Keep dry reps, leader rehearsals, and control measures ahead of ammunition or friction injects.\n"
            "- Tie the lane to one or two standards the staff can actually assess.\n"
            "- Make safety and stop-training criteria explicit before the first iteration.\n"
            "- Build the AAR to answer what control, communication, or accountability failed first.\n"
            "- Put qualified supervision and local SOP alignment ahead of enthusiasm.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(INFANTRY_REFERENCES),
            structured_citations=structured_citations(INFANTRY_REFERENCES),
            source_trust=source_trust_markers(
                INFANTRY_REFERENCES,
                notes_prefix=(
                    "Verify current infantry, urban-operations, and local training references "
                    "before execution."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this familiarization, sustainment, or an actual qualification standard?",
                (
                    "What is the training population's real baseline: non-03 support Marines, "
                    "provisional leaders, or infantry Marines?"
                ),
                "What is the first thing you should cut so the lane stays supervised and assessable?",
                "What must be dry-rehearsed before you add blanks, movement friction, or urban complexity?",
            ],
        )


def build_infantry_03xx_agent() -> Infantry03xxAdvisorAgent:
    return Infantry03xxAdvisorAgent()
