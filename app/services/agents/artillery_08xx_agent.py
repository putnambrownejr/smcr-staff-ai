from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    ARTILLERY_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class Artillery08xxAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="fires-advisor",
            name="Fires / Fire Support Advisor",
            description=(
                "MAGTF fires warfighting function — fire support coordination, artillery, NSFS, "
                "mortars, air-delivered fires, FSCC planning, call-for-fire training, "
                "and fires integration into combined-arms operations while refusing sensitive "
                "real-world fire missions, target lists, or classified fire plans."
            ),
            domain="fires, fire support, and combined-arms fires integration",
            intended_users=[
                "SMCR officers",
                "FSOs",
                "FDOs",
                "FOs",
                "S-3",
                "battery/battalion staff",
                "fire support coordinators",
            ],
            allowed_sources=[
                "public artillery and fire support doctrine",
                "public training and readiness references",
                "training-only fire support scenarios",
                "joint fires doctrine (unclassified)",
            ],
            disallowed_inputs=[
                "classified fire plans",
                "real-world target lists or coordinates",
                "sensitive fire mission data",
                "live fire control orders for real operations",
                "classified ammunition allocation or expenditure data",
            ],
            system_prompt=(
                "Respond like a fires-savvy training advisor under a demanding FSC or battalion FSO. "
                "Keep the tone precise, procedural, and standards-driven. Distinguish training-safe "
                "call-for-fire drills from live-fire execution, coordination from freelancing, and "
                "disciplined fire support planning from hand-waving. Stay training-safe and advisory.\n\n"
                "Call for fire (CFF) six elements: (1) Observer identification, (2) Warning order "
                "(adjust fire / fire for effect / suppress / immediate suppression), (3) Target location "
                "(grid, polar, or shift from known point), (4) Target description (type, size, activity, "
                "protection), (5) Method of engagement (type of adjustment, ammunition, distribution), "
                "(6) Method of fire and control (at my command, when ready, continuous, cease loading, "
                "check firing, end of mission).\n\n"
                "Fire support coordination measures (FSCMs):\n"
                "- Permissive: CFL (coordinated fire line) — fires short of CFL need no clearance from "
                "ground commander; beyond CFL requires coordination.\n"
                "- Restrictive: FSCL (fire support coordination line) — attacks beyond the FSCL do not "
                "require ground-force coordination; inside the FSCL, fires must be coordinated.\n"
                "- RFL (restrictive fire line): fires across this line require coordination with the "
                "affected unit.\n"
                "- NFL (no-fire line): fires that impact in or beyond this area are prohibited without "
                "clearance from the establishing HQ.\n\n"
                "D3A targeting cycle: Decide (develop HPTs, set targets and engagement criteria) → "
                "Detect (task ISR to find HPTs, confirm/deny NAIs) → Deliver (engage targets with "
                "appropriate means — fires, maneuver, IO) → Assess (BDA, determine re-engagement needs). "
                "The targeting cycle runs continuously and feeds the next iteration.\n\n"
                "Mortar vs artillery comparison:\n"
                "- 60mm mortar: ~3.5 km max range, organic to rifle company, fastest response\n"
                "- 81mm mortar: ~5.6 km max range, organic to weapons company/battalion, primary "
                "battalion indirect fire\n"
                "- 120mm mortar: ~7.2 km max range, provides heavier HE and illumination\n"
                "- 155mm howitzer (M777 towed): 22+ km max range (30+ km RAP), GCE's primary "
                "artillery; M109 self-propelled variant for mechanized units\n"
                "Mortars: short coordination chain, fastest response, best for close support. "
                "Artillery: deeper range, heavier effects, requires more coordination.\n\n"
                "Annex F (Fire Support) template structure: fire support tasks and purpose, "
                "fire support coordination measures (map overlay), target list (HVTs with grids, "
                "descriptions, engagement criteria), observer plan, ammunition allocation (CSR/RSR), "
                "FSCC organization and procedures, and coordination with adjacent/higher fires elements."
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
            "Fires / Fire Support advisory draft.\n\n"
            "Covers the fires warfighting function: artillery, NSFS, mortars, air-delivered fires, "
            "and fire support coordination across the MAGTF.\n\n"
            f"{active_context_block}"
            "Bottom line:\n"
            "- Fire support coordination is a staff discipline, not just a trigger pull.\n"
            "- If the FSCC cannot brief the fire support plan clearly, the plan is not ready.\n"
            "- Training value lives in the coordination, not the boom.\n\n"
            "Primary fires lenses:\n"
            "- Is this a call-for-fire drill, an FSCC coordination exercise, a fires integration "
            "event, or a combined-arms rehearsal?\n"
            "- What fire support coordination measures are in play, and can the staff brief them?\n"
            "- Is the fire support plan integrated with the scheme of maneuver, or bolted on?\n"
            "- What must be rehearsed at the coordination level before live or simulated execution?\n"
            "- Are observers, FDC, and the FSCC all using the same language and procedures?\n"
            "- What fires delivery means are available (cannon, mortar, NSFS, air) and how are they "
            "prioritized and deconflicted?\n\n"
            "What this lane is good for:\n"
            "- call-for-fire refreshers with proper format, corrections, and observer procedures\n"
            "- FSCC stand-up exercises and fire support coordination drills\n"
            "- fires integration into MAGTF planning: how fires fit the scheme of maneuver\n"
            "- fire support plan development for training events\n"
            "- combined-arms rehearsal design where fires meet ground and air\n"
            "- artillery MOS familiarization for non-08xx staff officers\n"
            "- NSFS request and coordination procedures for littoral or expeditionary scenarios\n"
            "- mortar employment and integration at the battalion and company level\n"
            "- air-delivered fires coordination with ACE and DASC\n\n"
            "Fires delivery means and ranges:\n"
            "- 60mm mortar: ~3.5 km max range, organic to rifle company, fastest response.\n"
            "- 81mm mortar: ~5.6 km max range, organic to weapons co/bn, primary bn indirect fire.\n"
            "- 120mm mortar: ~7.2 km max range, heavier HE and illumination capability.\n"
            "- 155mm howitzer (M777 towed): 22+ km (30+ km w/ RAP), GCE primary artillery.\n"
            "- NSFS: ship-to-shore fires for littoral/expeditionary ops — "
            "requires naval gunfire liaison and specific request procedures.\n"
            "- Air-delivered fires (CAS, AI): coordinated through DASC and the FSCC — "
            "longest lead time, highest coordination burden, biggest payoff when done right.\n\n"
            "Call for fire (CFF) — 6 elements:\n"
            "(1) Observer ID, (2) Warning order (adjust fire / FFE / suppress / immediate suppression), "
            "(3) Target location (grid, polar, shift from known point), (4) Target description, "
            "(5) Method of engagement, (6) Method of fire and control.\n\n"
            "Fire support coordination measures:\n"
            "- CFL (permissive): fires short of CFL need no ground clearance.\n"
            "- FSCL (restrictive): inside FSCL, fires must be coordinated with ground force.\n"
            "- RFL: fires across require affected-unit coordination.\n"
            "- NFL: fires impacting in/beyond prohibited without establishing-HQ clearance.\n\n"
            "D3A targeting cycle: Decide → Detect → Deliver → Assess. Runs continuously.\n\n"
            "08xx MOS depth:\n"
            "- 0802 Artillery Officer: whether the fire support plan is actually coordinated or just "
            "a slide; whether FSCMs are correct and briefable; whether the FSCC can run.\n"
            "- 0803 Target Acquisition: whether observation plans and target acquisition assets are "
            "integrated into the collection effort or operating in a vacuum.\n"
            "- 0842 Field Artillery Cannoneer / 0844 FDC: whether fire direction procedures are "
            "being drilled to standard, not just muscle memory.\n"
            "- 0861 Fire Support Man (FO): whether observers can execute a proper call for fire, "
            "adjust, and maintain communication discipline under pressure.\n\n"
            "My read:\n"
            "- Good fire support training for reserve units is usually about coordination discipline "
            "and procedural accuracy, not volume of fire.\n"
            "- The FSCC drill is often the most neglected and most valuable training event a "
            "battalion can run between live-fire opportunities.\n"
            "- If the fire support plan cannot be briefed in under five minutes at a rehearsal, "
            "it needs to be simplified before it needs to be executed.\n"
            "- Reserve artillery units that drill coordination, communication, and fire direction "
            "between annual training will get more out of their limited live-fire time.\n"
            "- Mortar training is the most accessible fires training for infantry battalions — "
            "the 81mm section can drill call-for-fire and FDC procedures at every drill.\n"
            "- NSFS coordination is a perishable skill that matters most in EABO/littoral scenarios.\n\n"
            "Checklist:\n"
            "- Name the training population and their fire support role (observer, FDC, FSCC, "
            "supported maneuver unit, NGLO, mortar section).\n"
            "- Decide whether the event is training procedures, coordination, integration, or execution.\n"
            "- Identify which fires delivery means are in play and their coordination requirements.\n"
            "- Ensure FSCMs are established and briefed before any simulated or live execution.\n"
            "- Rehearse the fire support plan at the coordination level before execution.\n"
            "- Tie the event to one or two assessable standards from T&R or local SOPs.\n"
            "- Make safety and cease-fire procedures explicit before the first iteration.\n"
            "- Build the AAR around coordination, communication, and procedural accuracy — "
            "not just effects on target.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(ARTILLERY_REFERENCES),
            structured_citations=structured_citations(ARTILLERY_REFERENCES),
            source_trust=source_trust_markers(
                ARTILLERY_REFERENCES,
                notes_prefix=(
                    "Verify current fire support doctrine, artillery references, and local "
                    "training directives before execution."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this a call-for-fire drill, an FSCC exercise, or a fires integration event?",
                "What is the training population's role: observers, FDC, FSCC staff, mortars, or supported maneuver?",
                "Which fires delivery means are in play: cannon, mortar, NSFS, or air-delivered?",
                "What fire support coordination measures need to be in place before execution?",
            ],
        )


def build_artillery_08xx_agent() -> Artillery08xxAdvisorAgent:
    return Artillery08xxAdvisorAgent()
