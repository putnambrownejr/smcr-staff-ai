from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S3_REFERENCES,
    STAFF_PROCESS_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)

# Planning-methodology references combine deliberate/rapid planning (S-3) with the
# staff-process facilitation layer (OPT conduct).
_PLANNING_REFERENCES = (*S3_REFERENCES, *STAFF_PROCESS_REFERENCES)

_RAPID_SIGNALS = (
    "rapid",
    "r2p2",
    "compressed",
    "time-constrained",
    "short timeline",
    "familiar",
    "quick turn",
    "already understand",
)


def _tempo_read(input_text: str) -> str:
    """Infer whether the situation calls for compressed or deliberate planning."""
    lowered = input_text.lower()
    if any(signal in lowered for signal in _RAPID_SIGNALS):
        return "rapid"
    return "deliberate"


class PlanningAdvisorAgent(Agent):
    """Single planning-methodology advisor.

    Collapses the former MCPP (deliberate), R2P2 (rapid), and OPT-facilitator
    agents into one. It guides the staff to the right planning *tempo*, runs the
    OPT facilitation discipline that applies regardless of tempo, and keeps
    product drafting from outrunning shared understanding.
    """

    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="planning-advisor",
            name="Planning Advisor (MCPP / R2P2 / OPT)",
            description=(
                "Helps a Marine staff pick the right planning tempo (deliberate MCPP vs compressed R2P2), "
                "run the OPT with visible assumptions, decisions, questions, and due-outs, and keep product "
                "drafting from outrunning shared understanding."
            ),
            domain="planning methodology",
            intended_users=["SMCR officers", "S-3", "XO", "chief of staff", "planning teams", "command teams"],
            allowed_sources=[
                "public Marine Corps planning doctrine",
                "public command and staff PME references",
                "public unit training management references",
                "local training-only planning context",
            ],
            disallowed_inputs=[
                "classified operational details",
                "real-world sensitive movements",
                "exact COMSEC or communications details",
            ],
            system_prompt=(
                "Respond like a practical Marine planner and OPT lead working for a hard-driving S-3. "
                "First get the tempo right: only endorse compressed R2P2 when the staff already understands "
                "the problem and has SOPs to support real compression; otherwise drive deliberate MCPP. "
                "Make the method explicit, force commander decisions into the open, keep the assumption and "
                "decision logs visible, and be blunt about drift, fake COAs, and product drafting that "
                "outruns thinking."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        tempo = _tempo_read(input_text)
        tempo_line = (
            "Tempo read: this looks compressed (R2P2-style). Compression is only legitimate when the staff "
            "already understands the problem — confirm that before skipping steps.\n\n"
            if tempo == "rapid"
            else "Tempo read: this looks like deliberate planning (MCPP). Build shared understanding before "
            "drafting products.\n\n"
        )
        answer = (
            "Planning advisor advisory.\n\n"
            "Use this to run the staff and pick the right planning tempo, not just to admire the process.\n\n"
            f"{tempo_line}"
            "Step 0 — pick the tempo honestly:\n"
            "- Deliberate MCPP when the staff still needs shared understanding of the problem.\n"
            "- Compressed R2P2 only when the problem is familiar, SOPs and baseline products exist, and TIME "
            "(not understanding) is the real constraint.\n"
            "- If the staff cannot explain the existing concept in a few clean sentences, it is not "
            "an R2P2 problem.\n\n"
            "Establish first (every tempo):\n"
            "- Who is the OPT lead, and who is recording assumptions, decisions, and staff questions?\n"
            "- What planning step are we actually in right now?\n"
            "- What commander problem are we solving, in one sentence?\n\n"
            "Deliberate MCPP rhythm:\n"
            "- Problem framing: what is actually being decided, and what is still ambiguous?\n"
            "- Mission analysis: assumptions, constraints, specified/implied/essential tasks, risk, info gaps.\n"
            "- COA development: build real options, not cosmetic variants.\n"
            "- COA wargaming: what breaks first, what support fails first, which decision point matters.\n"
            "- COA comparison and decision: tell the commander what each option gives, costs, and risks.\n"
            "- Orders development and transition: publish only after the staff frame is coherent.\n\n"
            "Compressed R2P2 rhythm (only when justified):\n"
            "- Reconfirm the mission and decision in plain language.\n"
            "- Identify only what changed; keep a short change log.\n"
            "- Validate the assumptions most likely to break the concept.\n"
            "- Run a short branch/sequel drill or TDG.\n"
            "- Publish only changed tasks, changed support, changed control measures, and changed suspenses.\n"
            "- Push unresolved friction into named actions immediately.\n\n"
            "Visible logs to maintain (every tempo):\n"
            "- assumption log\n"
            "- decision log\n"
            "- question log\n"
            "- due-out tracker\n"
            "- command relationship notes\n\n"
            "Abort compression and return to deliberate MCPP if:\n"
            "- The staff cannot agree on the problem.\n"
            "- Support, medical, comm, or subordinate relationships are still unclear.\n"
            "- The concept depends on assumptions nobody has actually checked.\n"
            "- 'Rapid' is being used to excuse confusion or skip thought instead of skipping rework.\n\n"
            "Watch for failure modes:\n"
            "- The staff is drafting slides or orders before it agrees on the problem.\n"
            "- COAs are fake because they differ only in wording, not in risk or method.\n"
            "- No clear OPT lead or battle rhythm, so discussion turns into drift.\n"
            "- One section carries the plan while the others wait to react.\n"
            "- S-4, S-6, and medical validate someone else's plan instead of shaping it early.\n"
            "- The meeting ends without a next battle-rhythm touchpoint.\n"
            "- People hide weak thinking behind polished product language.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(_PLANNING_REFERENCES),
            structured_citations=structured_citations(_PLANNING_REFERENCES),
            source_trust=source_trust_markers(
                _PLANNING_REFERENCES,
                notes_prefix="Verify current planning and command-and-staff doctrine and local SOPs before formal use.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What is the exact commander problem the staff is trying to solve?",
                "Which planning step is the staff actually in right now?",
                "Is time or understanding the real constraint — and does that justify the tempo you picked?",
                "Who is keeping the assumption and decision logs?",
                "What assumption would force you back to deliberate MCPP?",
            ],
        )


def build_planning_advisor_agent() -> PlanningAdvisorAgent:
    return PlanningAdvisorAgent()
