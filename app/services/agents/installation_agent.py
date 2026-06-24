from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    INSTALLATION_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class InstallationPracticalAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="installation-practical-advisor",
            name="Installation / Base Practical Advisor",
            description=(
                "Supports common USMC and joint-base practical questions such as access, visitor control, "
                "sponsorship, ID/REAL-ID friction, gate process, and command-event coordination."
            ),
            domain="installation practical knowledge",
            intended_users=["SMCR Marines", "staff officers", "command reps", "traveling Marines"],
            allowed_sources=[
                "official installation access pages",
                "official Marine Corps access-control policy",
                "local command notes and checklists",
            ],
            disallowed_inputs=[
                "classified visit details",
                "sensitive installation-security information not cleared for public tools",
                "PII not necessary for access planning",
            ],
            system_prompt=(
                "Respond like the practical staff Marine who knows where people usually get burned by base access, "
                "visitor process, and local coordination. Stay generic enough to be safe, but be explicit that local "
                "installation orders, PMO, visitor centers, and sponsor instructions always win.\n\n"
                "Major USMC installations and their key capabilities:\n"
                "- Camp Pendleton: West Coast major base, full ranges, combined-arms training areas.\n"
                "- Camp Lejeune: East Coast major base, amphibious training, MOUT facilities.\n"
                "- MCB Quantico: OCS, TBS, schools command, limited ranges.\n"
                "- Camp Butler (Okinawa): III MEF, overseas rotation hub.\n"
                "- MCLB Albany / MCLB Barstow: logistics bases, limited training infrastructure.\n"
                "- MCAGCC 29 Palms: combined-arms live-fire, ITX, largest USMC base by area.\n"
                "- MWTC Bridgeport: mountain/cold-weather training center.\n\n"
                "Reserve Training Center (RTC) vs major installation:\n"
                "- RTCs typically have: armory, small arms range, classroom space, drill deck.\n"
                "- RTCs typically lack: field training areas, live-fire ranges, billeting, medical.\n"
                "- Most RTCs are supported by 5-7 I&I (Inspector-Instructor) staff per company.\n"
                "- I&I duties: training support, admin continuity, equipment accountability, mobilization prep.\n\n"
                "Cross-service training: ISAs (inter-service agreements) and DD Form 1144 enable reserve units "
                "to use Army, Navy, or Air Force ranges and facilities when USMC facilities are unavailable.\n\n"
                "Site activation/deactivation and mobilization processing are MARFORRES functions — "
                "coordinate through the I&I staff and the gaining active-component command."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Installation / base practical advisory draft.\n\n"
            "Use this to reduce stupid friction around access, sponsorship, and local process. Do not treat it as the "
            "final authority over a specific installation.\n\n"
            "Bottom line:\n"
            "- Every base says it has a simple process right up until somebody shows up at the gate with the wrong ID, "
            "no sponsor, bad roster data, or a late request.\n"
            "- The local installation page, visitor center, PMO, and command sponsor beat generic advice every "
            "time.\n\n"
            "Common failure points:\n"
            "- non-REAL-ID visitors showing up without alternate identity documents\n"
            "- command events built without enough lead time for visitor vetting\n"
            "- no named sponsor or no by-name roster\n"
            "- drivers lacking the registration/insurance documents the gate expects\n"
            "- assuming one Marine Corps base does it the same way as another installation\n"
            "- not checking whether the event needs DBIDS, IARA, or a visitor-control-center stop\n\n"
            "Practical checklist:\n"
            "- Confirm the exact installation, gate, visitor-control process, and business hours.\n"
            "- Confirm whether the visitor has CAC/USID/REAL-ID or needs alternate identity proofing.\n"
            "- Identify the sponsor, roster owner, and local point of contact before the day of movement.\n"
            "- For command events, confirm lead time, by-name roster requirements, and any system like IARA.\n"
            "- If driving, verify license, registration, insurance, and any local vehicle restrictions.\n"
            "- If the visit touches a restricted area, tenant command, or classified space, route it through the "
            "local security process early.\n\n"
            "My read:\n"
            "- The unit usually loses time at the gate because somebody treated access like an admin detail instead "
            "of an operational dependency.\n"
            "- If access matters to the plan, then sponsorship, vetting, and arrival sequence belong in the plan.\n"
            "- Local base rules change enough that any confident generic answer should make you suspicious until it "
            "is checked.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(INSTALLATION_REFERENCES),
            structured_citations=structured_citations(INSTALLATION_REFERENCES),
            source_trust=source_trust_markers(
                INSTALLATION_REFERENCES,
                notes_prefix=(
                    "Treat these as starting points only and verify the exact local installation process before "
                    "movement."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Which installation or joint base is this for?",
                "Is this individual access, a command event, or a tenant-command visit?",
                "Who is the sponsor and what local access page or visitor-center guidance do you already have?",
            ],
        )


def build_installation_agent() -> InstallationPracticalAdvisorAgent:
    return InstallationPracticalAdvisorAgent()
