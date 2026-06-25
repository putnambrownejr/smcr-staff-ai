from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MOS_7200_REFERENCES,
    ORM_REFERENCES,
    S3_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class AceAgent(Agent):
    def __init__(self) -> None:
        refs = S3_REFERENCES + ORM_REFERENCES + STAFF_PRODUCT_REFERENCES + MOS_7200_REFERENCES
        self.metadata = AgentMetadata(
            id="ace",
            name="ACE / Air Combat Element",
            description=(
                "MAGTF Air Combat Element representative — air support, aviation effects, airspace coordination, "
                "air-ground integration, and ACE sustainment considerations."
            ),
            domain="aviation and air combat element",
            intended_users=["SMCR officers", "FSOs", "AirOs", "S-3", "wing staff", "ACE planners"],
            allowed_sources=[
                "public aviation and air-ground doctrine",
                "public training and readiness references",
                "training-only air support scenarios",
            ],
            disallowed_inputs=[
                "classified air tasking orders",
                "real-world flight schedules or sortie data",
                "sensitive airspace control measures",
                "live NOTAM or DAFIF data for real operations",
            ],
            system_prompt=(
                "Respond like an ACE representative advising the MAGTF CE. Focus on supported effects, "
                "air-ground integration, and coordination discipline. Stay training-safe and advisory.\n\n"
                "MACCS (Marine Air Command and Control System):\n"
                "- TACC (Tactical Air Command Center): senior aviation C2 node, ACE commander's CP. "
                "Integrates all ACE functions, produces ATO/ACO.\n"
                "- DASC (Direct Air Support Center): principal agency for aviation directly supporting "
                "the GCE. Collocates with GCE's senior FSCC. Processes immediate CAS/TRAP requests, "
                "manages FAC(A)/TAC(A) assets. Subordinate to TACC.\n"
                "- MASS (Marine Air Support Squadron): provides personnel and equipment to operate DASCs.\n"
                "- LAAD (Low Altitude Air Defense): close-in surface-to-air fires (Stinger/Avenger) "
                "protecting the MAGTF.\n"
                "- TADC (Tactical Air Direction Center): shipborne MACCS cell for amphibious ops.\n"
                "- TAOC (Tactical Air Operations Center): area air defense and airspace management.\n\n"
                "Six functions of Marine aviation:\n"
                "1. Offensive Air Support (OAS): CAS and deep air support — F-35B, AH-1Z, UH-1Y\n"
                "2. Assault Support: tactical mobility and logistics — MV-22B, CH-53E/K, UH-1Y, KC-130J\n"
                "3. Anti-Air Warfare (AAW): destroy/reduce hostile air threats — F-35B, LAAD, AH-1Z\n"
                "4. Electronic Warfare (EW): EA, EP, ES — F-35B EW suite, ECM pods\n"
                "5. Control of Aircraft and Missiles: MACCS C2 function integrating the other five\n"
                "6. Aerial Reconnaissance: ISR collection — RQ-21, F-35B sensors, FLIR pods\n\n"
                "MAGTF Air Tasking Cycle (six phases):\n"
                "I. Command aviation guidance (apportionment priorities)\n"
                "II. Air mission/target development (ACE staff + GCE fire support cells)\n"
                "III. Allocation/allotment (sorties by mission category)\n"
                "IV. ATO/ACO production (24-hr ATO, 72-96 hr planning horizon)\n"
                "V. Execution (DASC processes immediate requests, MACCS controls missions)\n"
                "VI. Combat assessment (BDA, feedback to next cycle)\n\n"
                "ACE aircraft task organization:\n"
                "- MV-22B (VMM): ~12/sqn, 24 troops or 20k lb, assault transport\n"
                "- AH-1Z (HMLA): ~12/sqn with ~6 UH-1Y, attack/armed recon, 20mm + Hellfire/JAGM\n"
                "- UH-1Y (HMLA): ~10/sqn, utility/CASEVAC, rockets + door guns\n"
                "- CH-53E/K (HMH): ~16/sqn, heavy lift (30-36k lb external)\n"
                "- F-35B (VMFA): ~16-20/sqn, stealth strike/CAS/AAW/ISR\n"
                "- KC-130J (VMGR): ~14/sqn, tanker/transport/Harvest HAWK armed overwatch\n\n"
                "ACE-GCE integration:\n"
                "- CAS: air attacks coordinated with GCE maneuver via DASC + FAC(A)/JTAC. "
                "9-line CAS request format from TACPs to DASC.\n"
                "- Deep air support: strikes beyond immediate battlefield (interdiction of reserves, "
                "logistics, C2). Planned through ATO cycle.\n"
                "- Shaping: SEAD/DEAD, EW jamming, illumination to set conditions.\n"
                "- Key interfaces: FSCC (unified fires), TACPs/JTACs (terminal control), "
                "ANGLICO (joint/coalition liaison), ALOs at key HQs.\n"
                "- CAS request flow: ground FSO → GCE FSCC → DASC → TACC/ATO or immediate asset."
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
            "ACE / Air Combat Element advisory draft.\n\n"
            "Use this to shape air-ground integration and ACE coordination, not to replace "
            "qualified aviation planners, local SOPs, or formal airspace coordination.\n\n"
            f"{active_context_block}"
            "Bottom line:\n"
            "- Start with the supported effect, not the aircraft wish list.\n"
            "- Air-ground integration becomes fragile when airspace, control, comm, fires, safety, "
            "and timelines are handled as separate conversations.\n"
            "- Keep real-world tasking details out of this tool.\n\n"
            "Primary ACE lenses:\n"
            "- What aviation effect supports the exercise objective or commander decision?\n"
            "- What airspace, fires, comm, range-control, and safety deconfliction must be solved first?\n"
            "- What request, approval, or support relationship has the longest lead time?\n"
            "- What no-go condition should stop the aviation portion?\n"
            "- How does the ACE sustain itself during the event (maintenance, crews, fuel, ordnance)?\n"
            "- Which MACCS agencies are required and where do they sit relative to the FSCC?\n"
            "- What phase of the air tasking cycle drives your planning timeline?\n\n"
            "MACCS structure:\n"
            "- TACC: senior ACE C2, produces ATO/ACO, integrates all functions\n"
            "- DASC: collocated with GCE FSCC, processes immediate CAS/TRAP requests\n"
            "- MASS: operates DASCs and DASC(A)\n"
            "- LAAD: close-in air defense (Stinger/Avenger)\n"
            "- TAOC: area air defense and airspace management\n"
            "CAS request flow: ground FSO → FSCC → DASC → TACC (ATO) or immediate assignment\n\n"
            "Six functions of Marine aviation:\n"
            "1. OAS (CAS + deep air support) — F-35B, AH-1Z\n"
            "2. Assault Support — MV-22B, CH-53E/K, UH-1Y, KC-130J\n"
            "3. AAW — F-35B, LAAD, AH-1Z escort\n"
            "4. EW — F-35B EW suite, ECM pods\n"
            "5. Control of Aircraft and Missiles — MACCS C2\n"
            "6. Aerial Reconnaissance — RQ-21, F-35B sensors, FLIR\n\n"
            "7200 Aviation Officer depth:\n"
            "- Whether the training event is supportable by aircraft, crews, maintenance, ranges, and weather.\n"
            "- Whether safety and ORM concerns are being handled as command decisions.\n"
            "- Whether MAWTS-style standardization and debrief discipline are being considered.\n"
            "- Whether wing staff sections can preserve continuity across drill gaps.\n\n"
            "Checklist:\n"
            "- Identify the supported effect and which of the six aviation functions applies.\n"
            "- Determine which MACCS agencies are needed and their locations relative to FSCC.\n"
            "- Build an air support estimate with supported effect, control method, comm/PACE.\n"
            "- Establish deconfliction questions, required approvals, and branch/no-go criteria.\n"
            "- Coordinate with S-3, fires, S-6, safety, GCE, LCE, and range/control authorities.\n"
            "- Ensure TACPs/JTACs are in place for terminal control of CAS.\n"
            "- Rehearse air-ground coordination before execution.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(self._refs),
            structured_citations=structured_citations(self._refs),
            source_trust=source_trust_markers(
                self._refs,
                notes_prefix="Verify current aviation doctrine and local coordination requirements.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What aviation effect supports the exercise objective?",
                "What airspace, fires, and comm deconfliction must be solved first?",
                "What request or approval has the longest lead time?",
                "What no-go condition should stop the aviation portion?",
            ],
        )


def build_ace_agent() -> AceAgent:
    return AceAgent()
