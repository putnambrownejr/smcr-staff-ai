from dataclasses import dataclass

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.schemas.staff import StaffEchelon, StaffRoleMetadata
from app.services.agents.base import Agent, AgentContext
from app.services.agents.osint_agent import build_osint_agent


@dataclass(frozen=True)
class StaffRoleDefinition:
    echelon: StaffEchelon
    role: str
    title: str
    maturity: str
    scope: str
    focus: tuple[str, ...]
    osint_enabled: bool = False


ROLE_DEFINITIONS: tuple[StaffRoleDefinition, ...] = (
    StaffRoleDefinition(
        StaffEchelon.company,
        "xo",
        "Company XO",
        "tactical/company",
        "Company execution and coordination",
        ("feasibility", "task ownership", "timeline"),
    ),
    StaffRoleDefinition(
        StaffEchelon.company,
        "firstsgt",
        "Company 1stSgt",
        "tactical/company",
        "Discipline, accountability, welfare, admin reality",
        ("Marine impact", "accountability", "admin friction"),
    ),
    StaffRoleDefinition(
        StaffEchelon.company,
        "cogysgt",
        "Company Gunnery Sergeant",
        "tactical/company",
        "Training, logistics, gear, field execution",
        ("resources", "gear", "field execution"),
    ),
    StaffRoleDefinition(
        StaffEchelon.company,
        "doc",
        "Company Doc",
        "tactical/company",
        "Medical support, casualty planning, and CASEVAC awareness",
        ("casualty response", "CASEVAC", "medical risk"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "xo",
        "Battalion XO",
        "battalion staff",
        "Staff synchronization and commander decision support",
        ("staff integration", "risk", "decision points"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "opso",
        "Battalion OpsO / S-3",
        "battalion staff",
        "Operations and training planning",
        ("scheme", "training value", "staff products"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "sgtmaj",
        "Battalion SgtMaj",
        "battalion command team",
        "Senior enlisted perspective",
        ("standards", "welfare", "discipline"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "s1",
        "S-1/AdminO",
        "battalion staff",
        "Administration and manpower",
        ("rosters", "orders", "FitReps", "awards"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "s2",
        "S-2",
        "battalion staff",
        "Intelligence and public-source context",
        ("assumptions", "information gaps", "source confidence"),
        True,
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "s3",
        "S-3",
        "battalion staff",
        "Operations and training",
        ("mission analysis", "training objectives", "timeline"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "s4",
        "S-4",
        "battalion staff",
        "Logistics and sustainment",
        ("transportation", "supply", "maintenance"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "s5",
        "S-5",
        "battalion staff",
        "Plans and future operations",
        ("future requirements", "sequencing", "branches"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "s6",
        "S-6",
        "battalion staff",
        "Communications and C2 support",
        ("C2", "PACE", "permissions"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "surgeon",
        "Battalion Surgeon / Medical Planner",
        "battalion staff",
        "Medical support, TCCC awareness, and evacuation planning",
        ("medical support", "TCCC", "evacuation planning"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g1",
        "G-1",
        "division/group staff",
        "Manpower and administration",
        ("policy", "manpower", "readiness"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g2",
        "G-2",
        "division/group staff",
        "Intelligence and public-source context",
        ("assumptions", "trends", "source confidence"),
        True,
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g3",
        "G-3",
        "division/group staff",
        "Operations and training",
        ("campaign rhythm", "readiness", "exercise alignment"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g4",
        "G-4",
        "division/group staff",
        "Logistics",
        ("sustainment", "distribution", "maintenance"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g5",
        "G-5",
        "division/group staff",
        "Plans",
        ("future operations", "sequencing", "coordination"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g6",
        "G-6",
        "division/group staff",
        "Communications",
        ("networks", "C2", "information management"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g9",
        "G-9 / Civil-Military",
        "division/group staff",
        "Civil-military integration, community context, and partner coordination",
        ("civil impact", "external coordination", "continuity"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "surgeon",
        "Division/Group Surgeon",
        "division/group staff",
        "Medical planning, health-service-support awareness, and evacuation oversight",
        ("medical planning", "CASEVAC", "supportability"),
    ),
)


class StaffAdvisorAgent(Agent):
    def __init__(self, definition: StaffRoleDefinition) -> None:
        self.definition = definition
        self.metadata = AgentMetadata(
            id=staff_agent_id(definition),
            name=definition.title,
            description=f"Advisory {definition.title} perspective for vetting staff ideas.",
            domain="staff council",
            intended_users=["SMCR officers", "staff officers", "command teams"],
            allowed_sources=[
                "local context",
                "public doctrine manifests",
                "session handoff",
                "OSINT source items when S-2/G-2",
            ],
            disallowed_inputs=[
                "classified information",
                "CUI",
                "sensitive operational details",
                "private personal data",
            ],
            system_prompt=(
                f"Respond as {definition.title} at {definition.maturity} level. Focus on {definition.scope}. "
                "Vet ideas constructively with concerns, recommendations, and human-review cautions."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        focus_lines = "\n".join(f"- {item}" for item in self.definition.focus)
        osint_note = ""
        citations: list[str] = []
        if self.definition.osint_enabled:
            osint_response = build_osint_agent().run(input_text, context)
            citations.extend(osint_response.citations)
            osint_note = (
                "\nS-2/G-2 OSINT tie-in:\n"
                "- This role should call the OSINT source-evaluation workflow for public-source claims.\n"
                "- Treat trend/social evidence as low confidence unless corroborated.\n"
            )
        answer = _build_staff_answer(self.definition, focus_lines, osint_note)
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citations,
            confidence=Confidence.low,
            follow_up_questions=[
                "What decision are you asking the commander or staff to make?",
                "What is the timeline and next suspense?",
                "What source or local context should this role review?",
            ],
        )


def staff_agent_id(definition: StaffRoleDefinition) -> str:
    return f"staff-{definition.echelon.value}-{definition.role}"


def build_staff_advisor_agents() -> list[StaffAdvisorAgent]:
    return [StaffAdvisorAgent(definition) for definition in ROLE_DEFINITIONS]


def list_staff_role_metadata() -> list[StaffRoleMetadata]:
    return [
        StaffRoleMetadata(
            agent_id=staff_agent_id(definition),
            echelon=definition.echelon,
            role=definition.role,
            name=definition.title,
            maturity=definition.maturity,
            scope=definition.scope,
            osint_enabled=definition.osint_enabled,
        )
        for definition in ROLE_DEFINITIONS
    ]


def _build_staff_answer(definition: StaffRoleDefinition, focus_lines: str, osint_note: str) -> str:
    if definition.role == "xo":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Be polite if you want; be clear regardless.\n"
            "- If this does not have a clear owner, suspense, and command decision point, it is not ready.\n"
            "- If the plan depends on everyone remembering what they meant between drills, it will drift.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What is the actual decision that needs to be made now?\n"
            "- What will break first in execution, not in theory?\n"
            "- Which staff assumption is doing too much work?\n"
            "- What needs to be cut, simplified, or assigned immediately?\n\n"
            "Recommended next action:\n"
            "- Reduce this to a workable plan with owners, suspense dates, and one commander decision.\n"
            "- Push unresolved friction back to the responsible staff section before calling it ready."
            f"{osint_note}"
        )

    if definition.role in {"opso", "s3"}:
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Train to a standard. If there is no standard, you are only burning time.\n"
            "- If it does not train a real standard, produce a needed output, or fit the available time,\n"
            "  it should not be on the schedule.\n"
            "- S-3 owns the training architecture: event design, timeline, products, and assessment.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What MET, METL, or required skill does this event actually improve?\n"
            "- What products, rehearsals, or support requests are on the critical path?\n"
            "- What is training value, and what is just activity?\n"
            "- What must be complete by the end of this drill to keep the event real?\n\n"
            "Recommended next action:\n"
            "- Build the short training plan now: end state, products, coordination matrix, eval plan,\n"
            "  and AAR structure.\n"
            "- Strip out anything that cannot be prepared, resourced, and assessed inside the reserve timeline."
            f"{osint_note}"
        )

    return (
        f"{definition.title} staff-vetting perspective.\n\n"
        f"Scope: {definition.scope}\n\n"
        "Primary lenses:\n"
        f"{focus_lines}\n\n"
        "Concerns to test:\n"
        "- Does the idea have a clear purpose, owner, timeline, and decision point?\n"
        "- What breaks during a reserve drill weekend with limited time and distributed personnel?\n"
        "- What official/public source should be checked before action?\n"
        "- What risk, admin, logistics, communications, or training dependency is being assumed?\n\n"
        "Recommended next action:\n"
        "- Turn the idea into a short staff estimate with assumptions, required coordination, risks, "
        "and a human reviewer."
        f"{osint_note}"
    )
