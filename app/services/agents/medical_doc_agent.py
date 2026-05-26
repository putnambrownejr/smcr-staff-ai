from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MEDICAL_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MedicalDocAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="medical-doc-advisor",
            name="Medical / Doc Advisor",
            description=(
                "Supports training-safe CASEVAC planning, TCCC-aware risk framing, 9-line familiarity, and "
                "medical-support coordination without claiming clinical authority."
            ),
            domain="medical support",
            intended_users=["SMCR officers", "Doc", "corpsman support planners", "S-3", "OIC", "command teams"],
            allowed_sources=[
                "public TCCC references",
                "public health service support doctrine",
                "public operations-planning references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "real patient records",
                "private medical details",
                "requests for diagnosis or treatment decisions",
                "sensitive real-world medevac details in unapproved environments",
            ],
            system_prompt=(
                "Respond like a practical field medical planner or doc supporting training and staff planning. "
                "Focus on CASEVAC structure, TCCC-aware planning, and coordination. Stay advisory and require "
                "qualified medical review. Sound like the person who will stop bad optimism before somebody gets hurt."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Medical / Doc advisory draft.\n\n"
            "Use this to shape training-safe medical support and CASEVAC planning, not as clinical direction.\n\n"
            "Primary medical-support lenses:\n"
            "- What casualty risks are actually plausible for this event or field problem?\n"
            "- Who is qualified, equipped, and positioned to address immediate life threats?\n"
            "- What assumptions exist about TCCC familiarity, evacuation timing, and transport availability?\n"
            "- What needs to be rehearsed at a generic 9-line / CASEVAC level before the event starts?\n\n"
            "TCCC knowledge to refresh:\n"
            "- Massive bleeding, airway, breathing, circulation, and hypothermia concerns\n"
            "  need a shared awareness vocabulary.\n"
            "- Self-aid, buddy-aid, corpsman actions, and higher-care handoff\n"
            "  should not blur together in the brief.\n"
            "- Trauma gear location and user familiarity matter as much as the written med plan.\n\n"
            "My read:\n"
            "- Medical plans fail when everyone assumes someone else owns the hard call.\n"
            "- If evacuation timing, transport, or casualty collection is hand-waved,\n"
            "  you do not have a medical plan yet.\n\n"
            "Checklist:\n"
            "- Define likely casualty scenarios and who owns first response actions.\n"
            "- Write the CASEVAC / MEDEVAC check: trigger, request path,\n"
            "  movement method, pickup logic, and accountability owner.\n"
            "- State the casualty collection logic from point of injury to handoff.\n"
            "- Confirm trauma gear, casualty collection, transport, and handoff assumptions.\n"
            "- Rehearse 9-line familiarity and reporting flow at a training-safe level only.\n"
            "- Publish the coordination trigger list for command, S-4, S-6, safety, and qualified medical review.\n"
            "- Tie CASEVAC planning to terrain, distance, comm, vehicles, and command decision points.\n"
            "- Define stop-training triggers before the event, not after the first casualty inject.\n"
            "- Pause for qualified medical review before treating the plan as final.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MEDICAL_REFERENCES),
            structured_citations=structured_citations(MEDICAL_REFERENCES),
            source_trust=source_trust_markers(
                MEDICAL_REFERENCES,
                notes_prefix="Verify current medical-support and TCCC training references before event execution.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this a field event, range, convoy, or general training problem?",
                "What casualty scenarios are most likely enough to drive planning?",
                "Who is the qualified medical reviewer for this plan?",
            ],
        )


def build_medical_doc_agent() -> MedicalDocAdvisorAgent:
    return MedicalDocAdvisorAgent()
