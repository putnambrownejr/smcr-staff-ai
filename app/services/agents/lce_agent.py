from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MEDICAL_REFERENCES,
    S4_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class LceAgent(Agent):
    def __init__(self) -> None:
        refs = S4_REFERENCES + MEDICAL_REFERENCES + STAFF_PRODUCT_REFERENCES
        self.metadata = AgentMetadata(
            id="lce",
            name="LCE / Logistics Combat Element",
            description=(
                "MAGTF Logistics Combat Element representative — sustainment, distribution, health services, "
                "recovery and reconstitution, and LCE integration with GCE and ACE."
            ),
            domain="logistics combat element",
            intended_users=["SMCR officers", "S-4", "LCE planners", "MLG staff", "CSS planners"],
            allowed_sources=[
                "public logistics and sustainment doctrine",
                "public health services references",
                "training-only logistics scenarios",
            ],
            disallowed_inputs=[
                "classified logistics plans",
                "real-world supply request data",
                "sensitive ammunition allocation data",
                "live patient or casualty data",
            ],
            system_prompt=(
                "Respond like an LCE representative advising the MAGTF CE. Focus on sustainment integration, "
                "distribution discipline, and health services coordination. Stay training-safe and advisory.\n\n"
                "LCE organization: The Marine Logistics Group (MLG) is the LCE of the MEF. It provides "
                "Combat Logistics Regiments (CLRs) and Combat Logistics Battalions (CLBs) to support "
                "the MAGTF. A CLB is the standard DS logistics battalion providing supply, maintenance, "
                "transportation, engineering, and health services to a supported GCE regiment or independent unit. "
                "A Combat Service Support Element (CSSE) task-organizes from the CLR/MLG for specific operations.\n\n"
                "Classes of supply and planning factors:\n"
                "- I (Rations): ~3 lbs/person/day field, MRE = 1 meal\n"
                "- II (Clothing/Equipment): demand-driven, mission-dependent\n"
                "- III (POL): fuel consumption varies by vehicle type; plan for 1 gal/vehicle/hour idle, "
                "3-5 gal/hour movement\n"
                "- IV (Construction): barrier material, lumber, wire — mission-dependent\n"
                "- V (Ammunition): CSR/RSR allocation drives planning; track by DODIC\n"
                "- VI (Personal items): PX-level supplies, low planning priority\n"
                "- VII (Major end items): vehicles, weapons systems — replacement pipeline\n"
                "- VIII (Medical): blood, pharmaceuticals, medical consumables\n"
                "- IX (Repair parts): driven by maintenance demand and readiness rates\n"
                "- X (Non-standard): civic action material, agricultural supplies\n\n"
                "Six logistics functions: supply, maintenance, transportation, general engineering, "
                "health services, services (postal, exchange, disbursing, legal, mortuary affairs).\n\n"
                "CSS estimate format: (1) Mission, (2) Situation, (3) Personnel/admin, (4) Logistics "
                "(supply, maintenance, transportation, services), (5) Health services, (6) Command/signal, "
                "(7) Assessment criteria, (8) Conclusions, (9) Recommendations.\n\n"
                "Logistics synchronization matrix: time-phase logistics actions against the operations "
                "timeline — when supplies are pushed, when convoys run, when maintenance windows open, "
                "when casualty collection activates. The matrix prevents logistics from being planned "
                "in isolation from the scheme of maneuver."
            ),
        )
        self._refs = refs

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = "Active local operating context:\n" + "\n".join(
                f"- {line}" for line in active_context_lines
            ) + "\n\n"

        answer = (
            "LCE / Logistics Combat Element advisory draft.\n\n"
            "Use this to shape sustainment planning and LCE integration, "
            "not to replace qualified logistics planners, local SOPs, or formal sustainment estimates.\n\n"
            f"{active_context_block}"
            "Bottom line:\n"
            "- If sustainment, distribution, and health services are briefed as separate stories, "
            "the LCE integration value is lost.\n"
            "- The LCE exists to sustain the fight, not to run a supply warehouse.\n\n"
            "Primary LCE lenses:\n"
            "- What sustainment assumption is carrying too much weight?\n"
            "- What distribution or health-service gap surfaces first under friction?\n"
            "- What recovery/reconstitution timeline is unrealistic?\n"
            "- How does the LCE synchronize with GCE and ACE needs?\n"
            "- What logistics decision belongs to the MAGTF commander rather than the LCE?\n"
            "- Are classes of supply planned by actual consumption rates or by guesswork?\n"
            "- Is the logistics synchronization matrix time-phased against the operations timeline?\n\n"
            "LCE organization:\n"
            "- MLG (Marine Logistics Group): MEF-level LCE, provides CLRs and CLBs.\n"
            "- CLR (Combat Logistics Regiment): task-organizes CLBs and functional companies.\n"
            "- CLB (Combat Logistics Battalion): standard DS logistics unit — supply, maintenance, "
            "transportation, engineering, health services to a supported regiment or independent unit.\n"
            "- CSSE (Combat Service Support Element): task-organized from CLR/MLG for specific ops.\n\n"
            "Six logistics functions:\n"
            "- Supply: classes I-X, requisition/receipt/issue/storage\n"
            "- Maintenance: equipment readiness, recovery, repair priorities\n"
            "- Transportation: movement control, convoy planning, distribution\n"
            "- General engineering: horizontal/vertical construction, utilities, EOD\n"
            "- Health services: casualty evacuation, treatment, medical logistics (Class VIII)\n"
            "- Services: postal, exchange, disbursing, legal, mortuary affairs\n\n"
            "What this lane is good for:\n"
            "- CSS estimate development (9-section format)\n"
            "- Logistics synchronization matrix construction\n"
            "- Classes of supply planning with consumption factors\n"
            "- Distribution and health services planning within the MAGTF\n"
            "- Recovery and reconstitution planning\n"
            "- CSS coordination with GCE and ACE elements\n"
            "- Reserve logistics unit training event design\n\n"
            "Checklist:\n"
            "- Build the CSS estimate: mission, situation, classes of supply, maintenance, "
            "transportation, health services, command/signal, assessment, recommendations.\n"
            "- Time-phase the logistics synchronization matrix against the scheme of maneuver.\n"
            "- Plan classes of supply by actual consumption rates, not by gut feel.\n"
            "- Identify CSS coordination points with GCE and ACE.\n"
            "- Plan distribution routes, health service support, and maintenance priorities.\n"
            "- Rehearse sustainment coordination at the MAGTF level.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(self._refs),
            structured_citations=structured_citations(self._refs),
            source_trust=source_trust_markers(
                self._refs,
                notes_prefix="Verify current logistics doctrine and local sustainment directives.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What sustainment assumption is carrying the most weight?",
                "What distribution or health-service gap surfaces first?",
                "How does the LCE synchronize with GCE and ACE needs?",
                "What recovery/reconstitution timeline is realistic?",
            ],
        )


def build_lce_agent() -> LceAgent:
    return LceAgent()
