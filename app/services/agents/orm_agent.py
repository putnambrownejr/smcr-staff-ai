from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    ORM_REFERENCES,
    RANGE_TRAINING_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)

_ORM_REFS = (*ORM_REFERENCES, *RANGE_TRAINING_REFERENCES)


class OrmRiskManagementAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="orm-risk-management",
            name="ORM / Safety / Risk Management",
            description=(
                "Produces advisory risk framing, control prompts, residual-risk thinking, "
                "ORM worksheets (DD Form 2977), RAC scoring, no-go criteria, rehearsal safety briefs, "
                "and safety officer products for training events."
            ),
            domain="safety and risk management",
            intended_users=["Safety officers", "staff officers", "leaders", "OICs", "range officers"],
            allowed_sources=[
                "public risk management doctrine",
                "training scenario inputs",
                "public safety references",
                "MCO 5100.29C (Marine Corps Safety Management System)",
                "MCO 3570.1D (Range Safety)",
                "unit safety SOPs",
            ],
            disallowed_inputs=[
                "medical PII",
                "real mishap details requiring protected handling",
                "official risk acceptance impersonation",
            ],
            system_prompt=(
                "Prompt structured ORM and safety thinking without replacing formal safety review. "
                "Focus on hazards, controls, residual risk, supervision, no-go criteria, "
                "rehearsal safety briefs, and commander decision points.\n\n"
                "ORM process (MCO 5100.29C Vol 2; OPNAVINST 3500.39 series) — five steps, 'IAMIS':\n"
                "1. Identify hazards (list what can hurt Marines, equipment, or mission — by phase of the event).\n"
                "2. Assess hazards (severity x probability → Risk Assessment Code).\n"
                "3. Make risk decisions (accept, mitigate, or elevate; the decision belongs to the leader with "
                "the authority for that residual risk level).\n"
                "4. Implement controls (engineering, administrative, PPE; name the owner of each control).\n"
                "5. Supervise (verify controls are in place, watch for change, and stop when triggers trip).\n"
                "Three levels: in-depth (deliberate planning far in advance), deliberate (DD Form 2977 "
                "worksheet before the event), time-critical (on the spot — ABCD: Assess the situation, "
                "Balance resources, Communicate, Do and debrief).\n\n"
                "Risk Assessment Code (RAC) matrix:\n"
                "- Severity: I catastrophic (death, permanent disability, major system loss); II critical "
                "(permanent partial disability, major damage); III moderate (lost-time injury, minor damage); "
                "IV negligible (first aid, minimal damage).\n"
                "- Probability: A frequent, B likely, C occasional, D seldom, E unlikely.\n"
                "- RAC: 1 critical, 2 serious, 3 moderate, 4 minor, 5 negligible. Rate the initial risk, apply "
                "controls, then rate the residual risk; the residual RAC drives who must accept it.\n"
                "- Acceptance authority rises with residual risk (as a common pattern: low → OIC, moderate → "
                "unit CO, high → first O-6 in the chain, extremely high → general officer). The local order "
                "sets the actual ladder — verify it.\n\n"
                "Range and live-fire specifics (MCO 3570.1D): certified OIC and RSO by name, surface danger "
                "zone and range control approval, medical standby with a CASEVAC plan and travel time to "
                "the MTF, cease-fire/check-fire procedures, heat and cold flag conditions, and stop-training "
                "authority for anyone who sees an unsafe act.\n\n"
                "Reserve realities: ORM worksheets built weeks earlier go stale by drill weekend — re-validate "
                "weather, personnel, and equipment at the safety brief; time-critical ORM is what actually "
                "happens on the range road at 0500."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "ORM / Safety / Risk Management advisory draft.\n\n"
            "Use this to shape risk thinking, safety products, and control development, "
            "not to replace formal safety review or risk acceptance.\n\n"
            "Five-step ORM (IAMIS — MCO 5100.29C Vol 2):\n"
            "1. Identify hazards by phase: movement, setup, execution, recovery, redeployment.\n"
            "2. Assess each hazard: severity (I–IV) x probability (A–E) → initial RAC.\n"
            "3. Make risk decisions: what is accepted, what is mitigated, what is elevated.\n"
            "4. Implement controls with a named owner for each.\n"
            "5. Supervise: verify controls before execution, watch for change, stop when triggers trip.\n\n"
            "RAC quick reference:\n"
            "- Severity: I catastrophic · II critical · III moderate · IV negligible\n"
            "- Probability: A frequent · B likely · C occasional · D seldom · E unlikely\n"
            "- RAC: 1 critical · 2 serious · 3 moderate · 4 minor · 5 negligible\n"
            "- Rate initial risk → apply controls → rate residual risk → route to the leader authorized to "
            "accept that residual level (verify the local ladder; common pattern low → OIC, moderate → CO, "
            "high → O-6, extremely high → GO).\n\n"
            "Primary ORM lenses:\n"
            "- What hazard actually threatens the event, and what is just background inconvenience?\n"
            "- What control must exist before execution versus what only makes the event smoother?\n"
            "- Who owns supervision, residual-risk acceptance, and stop-training authority?\n\n"
            "Safety officer products:\n"
            "- ORM worksheet (DD Form 2977): hazard, initial RAC, controls, residual RAC, control owner, "
            "how supervised.\n"
            "- No-go criteria: conditions that stop the event before or during execution (weather flags, "
            "medical coverage, comm with range control, minimum leader/instructor ratio).\n"
            "- Residual-risk decision note: what risk remains after controls, who accepts it, when re-validated.\n"
            "- Rehearsal safety brief: safety-specific items for inclusion in rehearsals.\n"
            "- Range/event safety plan: OIC/RSO by name, SDZ approval, medical standby and CASEVAC route, "
            "cease-fire procedures (MCO 3570.1D).\n"
            "- Time-critical ORM card for leaders on the day: Assess, Balance resources, Communicate, Do and debrief.\n\n"
            "My read:\n"
            "- Weak ORM usually lists hazards without changing the plan.\n"
            "- If nobody can name the no-go criteria, then the control plan is not mature yet.\n"
            "- A worksheet with every hazard rated 'low' after controls has usually not been honest about probability.\n"
            "- Safety officer products that nobody reads are just checkbox compliance — "
            "good safety products change the plan or the brief.\n\n"
            "Checklist:\n"
            "- Identify the main hazards, likely consequences, and the controls that actually matter.\n"
            "- Score initial and residual RAC and route the worksheet to the right acceptance authority.\n"
            "- Separate leader verification checks from command decision points.\n"
            "- Name supervision, residual-risk owner, and stop-training triggers.\n"
            "- Develop explicit no-go criteria and rehearsal safety brief items.\n"
            "- Re-validate the worksheet at the safety brief: weather, personnel, equipment, medical coverage.\n"
            "- Carry unresolved high-risk items to command review instead of hiding them in a worksheet.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(_ORM_REFS),
            structured_citations=structured_citations(_ORM_REFS),
            source_trust=source_trust_markers(
                _ORM_REFS,
                notes_prefix="Verify current safety references and local authority for final risk decisions.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What event, lane, or movement problem is driving the risk review?",
                "What hazard is most likely to become a no-go issue if left vague?",
                "What is the highest residual RAC, and who in the chain is authorized to accept it?",
            ],
        )


def build_orm_agent() -> OrmRiskManagementAgent:
    return OrmRiskManagementAgent()
