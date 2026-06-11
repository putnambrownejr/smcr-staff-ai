from dataclasses import dataclass

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.schemas.staff import MagtfLens, StaffEchelon, StaffRoleMetadata
from app.services.agents.base import Agent, AgentContext
from app.services.agents.osint_agent import build_osint_agent
from app.services.agents.source_refs import (
    FORCE_PROTECTION_REFERENCES,
    G8_REFERENCES,
    G9_REFERENCES,
    IG_REFERENCES,
    LEADERSHIP_REFERENCES,
    LEGAL_REFERENCES,
    MEDICAL_REFERENCES,
    ORM_REFERENCES,
    PAO_REFERENCES,
    S1_REFERENCES,
    S2_REFERENCES,
    S3_REFERENCES,
    S4_REFERENCES,
    S6_REFERENCES,
    SEL_REFERENCES,
    STAFF_PROCESS_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    SourceRef,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


@dataclass(frozen=True)
class StaffRoleDefinition:
    echelon: StaffEchelon
    role: str
    title: str
    maturity: str
    scope: str
    focus: tuple[str, ...]
    magtf_lenses: tuple[MagtfLens, ...] = (MagtfLens.ce_c2,)
    products: tuple[str, ...] = ()
    osint_enabled: bool = False


ROLE_DEFINITIONS: tuple[StaffRoleDefinition, ...] = (
    StaffRoleDefinition(
        StaffEchelon.company,
        "xo",
        "Company XO",
        "tactical/company",
        "Company execution and coordination",
        ("feasibility", "task ownership", "timeline"),
        (MagtfLens.ce_c2,),
        ("XO sync matrix", "decision support matrix", "due-out tracker"),
    ),
    StaffRoleDefinition(
        StaffEchelon.company,
        "firstsgt",
        "Company 1stSgt",
        "tactical/company",
        "Discipline, accountability, welfare, admin reality",
        ("Marine impact", "accountability", "admin friction"),
        (MagtfLens.ce_c2,),
        ("troop-flow checklist", "formation/transition matrix", "leader touchpoint plan"),
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
        (MagtfLens.gce, MagtfLens.lce),
        ("Company casualty response plan", "CASEVAC rehearsal checklist", "medical risk note"),
    ),
    StaffRoleDefinition(
        StaffEchelon.company,
        "safety",
        "Company Safety Representative",
        "tactical/company",
        "Collateral-duty safety, ORM, and stop-training criteria",
        ("ORM", "range/training safety", "stop-training criteria"),
        (MagtfLens.gce, MagtfLens.ce_c2),
        ("ORM worksheet", "no-go criteria", "residual-risk decision note", "rehearsal safety brief"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "xo",
        "Battalion XO",
        "battalion staff",
        "Staff synchronization and commander decision support",
        ("staff integration", "risk", "decision points"),
        (MagtfLens.ce_c2,),
        ("XO sync matrix", "decision support matrix", "due-out tracker"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "chief",
        "Battalion Chief / Chief of Staff Aide",
        "battalion staff",
        "Command-group continuity, due-out discipline, and turnover quality",
        ("continuity", "due-outs", "brief posture"),
        (MagtfLens.ce_c2,),
        ("due-out tracker", "command update brief", "turnover handoff notes"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "battle_captain",
        "Battalion Battle Captain",
        "battalion staff",
        "Watchfloor control, command-post picture, and escalation discipline",
        ("watchstanding", "status picture", "escalation"),
        (MagtfLens.ce_c2,),
        ("decision support matrix", "battle captain watchboard", "command update brief"),
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
        (MagtfLens.ce_c2,),
        ("troop-flow checklist", "formation/transition matrix", "leader touchpoint plan"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "s1",
        "S-1/AdminO",
        "battalion staff",
        "Administration and manpower",
        ("rosters", "orders", "FitReps", "awards"),
        (MagtfLens.ce_c2,),
        (
            "admin estimate",
            "admin task tracker",
            "routing matrix",
            "pre-drill admin readiness check",
        ),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "s2",
        "S-2",
        "battalion staff",
        "Intelligence and public-source context",
        ("assumptions", "information gaps", "source confidence"),
        osint_enabled=True,
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
        (MagtfLens.lce, MagtfLens.gce),
        ("Medical estimate", "CASEVAC / MEDEVAC check", "casualty collection logic", "coordination trigger list"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "sja",
        "Battalion SJA / Legal Officer",
        "battalion special staff",
        "Legal issue-spotting, ROE/RUF guardrails, investigations, and command legal routing",
        ("legal review", "ROE/RUF", "investigation boundaries"),
        (MagtfLens.ce_c2,),
        ("Legal issue-spotter", "ROE/RUF guardrails", "legal review trigger list"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "pao",
        "Battalion PAO / COMMSTRAT Representative",
        "battalion special staff",
        "Public affairs posture, release authority, media handling, and OPSEC coordination",
        ("public posture", "release authority", "OPSEC coordination"),
        (MagtfLens.ce_c2,),
        ("Public affairs plan", "release approval matrix", "media and visitor playbook", "response-to-query lines"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "chaplain",
        "Battalion Chaplain",
        "battalion special staff",
        "Religious support, morale, ethical climate, and confidential support boundaries",
        ("religious support", "morale", "confidentiality boundaries"),
        (MagtfLens.ce_c2,),
        ("Religious support plan", "morale and welfare estimate", "confidentiality boundary note"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "rp",
        "Religious Program Specialist",
        "battalion special staff",
        "Religious-ministry logistics, schedule support, and chaplain support continuity",
        ("service logistics", "schedule support", "continuity"),
        (MagtfLens.ce_c2, MagtfLens.lce),
        ("Religious support schedule", "RMT logistics checklist", "continuity note"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "safety",
        "Battalion Safety Officer",
        "battalion special staff",
        "ORM, mishap prevention, risk acceptance, and stop-training criteria",
        ("ORM", "risk acceptance", "mishap prevention"),
        (MagtfLens.ce_c2, MagtfLens.gce),
        ("ORM worksheet", "no-go criteria", "residual-risk decision note", "rehearsal safety brief"),
    ),
    StaffRoleDefinition(
        StaffEchelon.battalion,
        "provost",
        "Provost Marshal / Security Advisor",
        "battalion special staff",
        "Force protection, access control, traffic control, detainee/security planning",
        ("force protection", "access control", "security coordination"),
        (MagtfLens.ce_c2, MagtfLens.lce),
        ("Security annex", "access-control plan", "traffic and parking control plan", "visitor control checklist"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "meu_s3",
        "MEU S-3",
        "regiment/MEU/wing staff",
        "MAGTF exercise architecture, execution rhythm, and integrated training objectives",
        ("MAGTF scheme", "training objectives", "execution rhythm"),
        (MagtfLens.ce_c2, MagtfLens.gce, MagtfLens.ace, MagtfLens.lce),
        ("MAGTF exercise concept", "event synchronization matrix", "commander decision brief"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "meu_s4",
        "MEU S-4",
        "regiment/MEU/wing staff",
        "MAGTF sustainment, embark, distribution, and supportability",
        ("sustainment", "embark", "supportability"),
        (MagtfLens.lce, MagtfLens.ce_c2),
        ("MAGTF logistics estimate", "embark/support matrix", "recovery plan"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "blt",
        "BLT / GCE Representative",
        "regiment/MEU/wing staff",
        "Ground combat element training value, scheme feasibility, and supported unit reality",
        ("GCE scheme", "training realism", "supported-unit friction"),
        (MagtfLens.gce, MagtfLens.ce_c2),
        ("GCE estimate", "BLT training objectives", "ground-control checklist"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "ace",
        "ACE Representative",
        "regiment/MEU/wing staff",
        "Aviation combat element integration, aviation supportability, and air-ground friction",
        ("aviation supportability", "air-ground integration", "airspace/deconfliction"),
        (MagtfLens.ace, MagtfLens.ce_c2),
        ("ACE estimate", "air support coordination checklist", "aviation no-go criteria"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "airo",
        "Air Officer",
        "regiment/MEU/wing special staff",
        "Air support requests, aviation effects, airspace/control coordination, and air-ground integration",
        ("supported aviation effect", "airspace/control", "air-ground deconfliction"),
        (MagtfLens.ace, MagtfLens.ce_c2, MagtfLens.gce),
        ("Air support estimate", "air-ground coordination matrix", "airspace/control questions"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "lce",
        "LCE Representative",
        "regiment/MEU/wing staff",
        "Logistics combat element sustainment, distribution, health services, and recovery",
        ("sustainment", "distribution", "health services"),
        (MagtfLens.lce, MagtfLens.ce_c2),
        ("LCE estimate", "sustainment support matrix", "recovery and reconstitution checklist"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "sja",
        "Regimental/MEU/Wing SJA",
        "regiment/MEU/wing special staff",
        "Legal review, ROE/RUF, ethics, investigations, claims, release coordination, and LOAC issue-spotting",
        ("legal review", "ROE/RUF", "ethics and investigations"),
        (MagtfLens.ce_c2,),
        ("Legal estimate", "ROE/RUF guardrails", "legal review and claims trigger list"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "pao",
        "Regimental/MEU/Wing PAO",
        "regiment/MEU/wing special staff",
        "Public affairs, media posture, release authority, imagery, and OPSEC coordination",
        ("media posture", "release authority", "OPSEC coordination"),
        (MagtfLens.ce_c2,),
        ("Public affairs plan", "media engagement plan", "release approval matrix", "response-to-query lines"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "commstrat",
        "COMMSTRAT / Information Officer",
        "regiment/MEU/wing special staff",
        "Communication strategy, public impact, narrative coherence, and information effects coordination",
        ("public impact", "narrative coherence", "information effects"),
        (MagtfLens.ce_c2,),
        (
            "COMMSTRAT estimate",
            "themes and messages",
            "response-to-query lines",
            "information effects coordination matrix",
        ),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "ig",
        "Inspector General",
        "regiment/MEU/wing special staff",
        "Inspection readiness, inquiry boundaries, impartiality, trends, and command climate signals",
        ("inspection readiness", "inquiry boundaries", "impartiality"),
        (MagtfLens.ce_c2,),
        ("IG inspection touchpoints", "inquiry boundary note", "readiness trend memo"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "chaplain",
        "Regimental/MEU/Wing Chaplain",
        "regiment/MEU/wing special staff",
        "Religious support planning, morale, ethical climate, and RMT integration",
        ("religious support", "morale", "RMT integration"),
        (MagtfLens.ce_c2,),
        ("Religious support plan", "RMT support matrix", "morale and welfare estimate"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "surgeon",
        "Regimental/MEU/Wing Surgeon",
        "regiment/MEU/wing special staff",
        "Health service support, casualty estimates, medical evacuation, and medical readiness",
        ("health service support", "casualty estimates", "medical evacuation"),
        (MagtfLens.lce, MagtfLens.ce_c2),
        ("Medical estimate", "medical service support annex", "CASEVAC / MEDEVAC check", "coordination trigger list"),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "provost",
        "Provost Marshal / Security Advisor",
        "regiment/MEU/wing special staff",
        "Security, force protection, law enforcement, traffic control, and detainee planning",
        ("force protection", "security", "traffic control"),
        (MagtfLens.ce_c2, MagtfLens.lce),
        (
            "Security annex",
            "force-protection checklist",
            "traffic and parking control plan",
            "visitor control checklist",
        ),
    ),
    StaffRoleDefinition(
        StaffEchelon.regiment_meu_wing,
        "safety",
        "Safety Officer",
        "regiment/MEU/wing special staff",
        "ORM, mishap prevention, range/training safety, and risk acceptance",
        ("ORM", "mishap prevention", "risk acceptance"),
        (MagtfLens.ce_c2, MagtfLens.gce, MagtfLens.ace, MagtfLens.lce),
        ("Risk assessment worksheet", "no-go criteria", "residual-risk acceptance note"),
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
        osint_enabled=True,
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
        (MagtfLens.lce, MagtfLens.ce_c2),
        ("Medical estimate", "health service support annex", "medical readiness risks"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g7",
        "G-7 / Information",
        "division/group staff",
        "Information, COMMSTRAT, public impact, and information-environment integration",
        ("information", "COMMSTRAT", "public impact"),
        (MagtfLens.ce_c2,),
        (
            "Information estimate",
            "COMMSTRAT guidance",
            "themes and messages",
            "information effects coordination matrix",
        ),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "g8",
        "G-8 / Resources",
        "division/group staff",
        "Resources, fiscal constraints, prioritization, and funding-risk tradeoffs",
        ("resources", "prioritization", "funding risk"),
        (MagtfLens.ce_c2,),
        ("resource estimate", "funding risk note", "priority tradeoff brief", "resourcing decision point"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "wing_ops",
        "Wing Operations",
        "division/group staff",
        "MAW/ACE operations integration, sortie-generation constraints, and aviation exercise feasibility",
        ("ACE operations", "sortie generation", "aviation feasibility"),
        (MagtfLens.ace, MagtfLens.ce_c2),
        ("wing operations estimate", "aviation supportability matrix", "airspace/deconfliction issues"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "mlg_log",
        "MLG Logistics",
        "division/group staff",
        "MLG/LCE logistics, distribution, medical, maintenance, and sustainment realism",
        ("LCE sustainment", "distribution", "maintenance"),
        (MagtfLens.lce, MagtfLens.ce_c2),
        ("MLG logistics estimate", "distribution support matrix", "sustainment risk note"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "sja",
        "Division/Group SJA",
        "division/group special staff",
        "Legal review, ROE/RUF, ethics, investigations, claims, and command legal routing",
        ("legal review", "ROE/RUF", "investigations"),
        (MagtfLens.ce_c2,),
        ("legal estimate", "ROE/RUF guardrails", "legal review trigger list"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "pao",
        "Division/Group PAO",
        "division/group special staff",
        "Public affairs posture, release authority, media operations, imagery, and OPSEC coordination",
        ("public affairs", "media operations", "OPSEC coordination"),
        (MagtfLens.ce_c2,),
        ("public affairs plan", "media operations plan", "release approval matrix", "response-to-query lines"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "ig",
        "Division/Group Inspector General",
        "division/group special staff",
        "Inspection readiness, inquiries, impartiality, and readiness trends",
        ("inspection readiness", "inquiry boundaries", "readiness trends"),
        (MagtfLens.ce_c2,),
        ("inspection readiness plan", "IG inquiry boundary note", "readiness trend memo"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "safety",
        "Division/Group Safety Officer",
        "division/group special staff",
        "Risk management, mishap prevention, risk acceptance, and safety-program integration",
        ("risk management", "mishap prevention", "risk acceptance"),
        (MagtfLens.ce_c2, MagtfLens.gce, MagtfLens.ace, MagtfLens.lce),
        ("risk management estimate", "no-go criteria", "residual-risk acceptance note"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "commstrat",
        "Division/Group COMMSTRAT",
        "division/group special staff",
        "Communication strategy, public impact, narrative coherence, and information integration",
        ("communication strategy", "public impact", "information integration"),
        (MagtfLens.ce_c2,),
        ("COMMSTRAT estimate", "themes and messages", "response-to-query lines", "information coordination matrix"),
    ),
    StaffRoleDefinition(
        StaffEchelon.division_group,
        "airo",
        "Air Officer",
        "division/group special staff",
        "Air support requests, aviation effects, airspace/control coordination, and air-ground integration",
        ("supported aviation effect", "airspace/control", "air-ground deconfliction"),
        (MagtfLens.ace, MagtfLens.ce_c2, MagtfLens.gce),
        ("air support estimate", "air-ground coordination matrix", "aviation assumptions/no-go list"),
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
                "Vet ideas constructively with concerns, recommendations, and human-review cautions. "
                "For XO roles, sound fair, steady, and judgment-heavy. For S-3/OpsO roles, sound blunt, impatient "
                "with fluff, and hard on weak planning."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        focus_lines = "\n".join(f"- {item}" for item in self.definition.focus)
        osint_note = ""
        citations: list[str] = []
        structured = []
        trust = []
        if self.definition.osint_enabled:
            osint_response = build_osint_agent().run(input_text, context)
            citations.extend(osint_response.citations)
            osint_note = (
                "\nS-2/G-2 OSINT tie-in:\n"
                "- This role should call the OSINT source-evaluation workflow for public-source claims.\n"
                "- Treat trend/social evidence as low confidence unless corroborated.\n"
            )
        role_refs = _role_references(self.definition.role)
        if role_refs:
            citations.extend(citation_titles(role_refs))
            structured.extend(structured_citations(role_refs))
            trust.extend(
                source_trust_markers(
                    role_refs,
                    notes_prefix="Verify current doctrine, training, and local applicability before action.",
                )
            )
        answer = _build_staff_answer(self.definition, focus_lines, osint_note)
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citations,
            structured_citations=structured,
            source_trust=trust,
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
    active_context_note = (
        "\nUse the stored active local operating context if one exists to bias the answer toward the user's current "
        "unit, billet, and short-term mission set.\n"
    )
    if definition.role == "xo":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Stay even-handed. Hear all sides, then cut to the governing point.\n"
            "- Fair does not mean soft. If the logic is weak, say so plainly.\n"
            "- If this does not have a clear owner, suspense, and command decision point, it is not ready.\n"
            "- If the plan depends on everyone remembering what they meant between drills, it will drift.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What is the actual decision that needs to be made now?\n"
            "- What will break first in execution, not in theory?\n"
            "- Which staff assumption is doing too much work?\n"
            "- What is the fairest and most workable cut through the competing preferences in the room?\n"
            "- What needs to be cut, simplified, or assigned immediately?\n\n"
            "Recommended next action:\n"
            "- Reduce this to a workable plan with owners, suspense dates, and one commander decision.\n"
            "- Push unresolved friction back to the responsible staff section before calling it ready."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "chief":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- My job is continuity and pressure, not theater.\n"
            "- If the due-out tracker lies, the whole command picture lies a little behind it.\n"
            "- Every suspense needs an owner, every late item needs a disposition, and every turnover "
            "needs the truth.\n"
            "- If the brief posture and the actual staff posture differ, fix the staff posture first.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What is actually late right now?\n"
            "- What has drifted because nobody wanted to reassign it clearly?\n"
            "- What must the next commander or XO touchpoint understand in one minute?\n"
            "- What is still being carried verbally instead of on a tracker or turnover note?\n"
            "- Which staff lane needs pressure, not another polite reminder?\n\n"
            "Recommended next action:\n"
            "- Clean the due-out tracker, strip it to real suspense items, and mark every line owner and status.\n"
            "- Rewrite the turnover note so the relieving watch inherits one true picture, not three versions of it."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "battle_captain":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- The watchboard is the fight. If it is stale, the command cell is stale.\n"
            "- I do not need every detail; I need what changed, what matters, and what escalates next.\n"
            "- If a trigger is not written down, the command post will discover it late and call that surprise.\n"
            "- Turnover quality is operational quality in smaller clothing.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What changed since the last huddle?\n"
            "- What is the next decision trigger and who gets called when it trips?\n"
            "- What watch item is being mistaken for a solved problem?\n"
            "- What will the relieving watch misunderstand first if we hand this over right now?\n"
            "- What belongs on the command update brief and what belongs off to the side?\n\n"
            "Recommended next action:\n"
            "- Build a watchboard with current status, next suspense, next decision, and next escalation trigger.\n"
            "- Force turnover notes to capture what changed, what was elevated, and what the next watch must verify."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role in {"opso", "s3"}:
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Train to a standard. If there is no standard, you are only burning time.\n"
            "- Do not hand me decorative complexity and call it planning.\n"
            "- If it does not train a real standard, produce a needed output, or fit the available time,\n"
            "  it should not be on the schedule.\n"
            "- S-3 owns the training architecture: event design, timeline, products, and assessment.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What MET, METL, or required skill does this event actually improve?\n"
            "- What products, rehearsals, or support requests are on the critical path?\n"
            "- What is training value, and what is just activity?\n"
            "- Which part of this is pretending to be ready because nobody wants the argument?\n"
            "- What must be complete by the end of this drill to keep the event real?\n\n"
            "Recommended next action:\n"
            "- Build the short training plan now: end state, products, coordination matrix, eval plan,\n"
            "  and AAR structure.\n"
            "- Strip out anything that cannot be prepared, resourced, and assessed inside the reserve timeline."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "s4":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- If the support architecture is fuzzy, the event is still a hope, not a plan.\n"
            "- The item with the longest lead time owns the timeline whether the staff likes it or not.\n"
            "- Nice concepts usually die on transport, issue/turn-in, water, chow, or recovery time.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What absolutely cancels the event if unresolved?\n"
            "- Which support ask has the earliest no-later-than decision point?\n"
            "- What accountability or movement assumption is still doing too much work?\n"
            "- What should be cut now to protect supportability?\n\n"
            "Recommended next action:\n"
            "- Publish the minimum support package, longest lead-time suspense, and recovery timeline.\n"
            "- Force a yes, no, or not-yet from every support owner before calling the plan executable."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "s6":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Most reserve comm plans fail from confusion, not from exotic technical problems.\n"
            "- If reporting windows, fallback methods, and user access are not rehearsed,\n"
            "  the PACE plan is decoration.\n"
            "- Too many tools usually means nobody knows which one the commander actually cares about.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What information must move without fail, and in what time window?\n"
            "- What dies first: access, battery, permissions, user training, or report discipline?\n"
            "- What fallback method is simple enough to survive friction?\n"
            "- What should stay generic until validated through proper channels?\n\n"
            "Recommended next action:\n"
            "- Reduce the comm plan to one essential reporting flow, one fallback, and one missed-report action.\n"
            "- Solve CAC, PKI, access, and permissions problems before drill rather than during execution."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "s1":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Admin drift kills more plans than bad intent does.\n"
            "- If nobody owns the final route, suspense, and source check, the package is already late.\n"
            "- Reserve continuity fails quietly, then all at once, when notes are stale and handoffs are vague.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What admin action actually matters now, and what can stay in continuity tracking?\n"
            "- What source, routing chain, or suspense is still ambiguous?\n"
            "- What will be forgotten between drills if it is not written down today?\n"
            "- What travel-admin issue will hijack the next planning cycle if ignored?\n\n"
            "Recommended next action:\n"
            "- Publish one admin task tracker with owner, due date, source reference, and command touchpoint.\n"
            "- Separate travel, orders, roster, FitRep, readiness, and awards lanes "
            "before they contaminate each other.\n"
            "- Run a pre-drill admin readiness check before dismissal so the next cycle does not start cold."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role in {"s2", "g2"}:
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- A weak estimate becomes dangerous the moment it starts sounding confident.\n"
            "- The staff needs one clear assessment, one key caveat, and one information gap that matters.\n"
            "- If the source picture is soft, brief the uncertainty instead of pretending it is settled.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What is actually known from public sources?\n"
            "- Which claim is still single-source, stale, or noisy?\n"
            "- What assumption would most change the commander's decision if it proves wrong?\n"
            "- What should be caveated instead of concluded?\n\n"
            "Recommended next action:\n"
            "- Reduce the estimate to corroborated facts, explicit assumptions, and one collection gap for follow-up.\n"
            "- Keep OSINT in the sourced-public lane and kill anything that looks like guesswork."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role in {"firstsgt", "sgtmaj"}:
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Standards events fail when the unit treats sequence and accountability like details.\n"
            "- Marines can recover from friction faster than they can recover from looking unprepared in public.\n"
            "- If ceremony, customs, courtesies, or formation control matter here,\n"
            "  then rehearsal and ownership matter too.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What standard, custom, or formal process governs this event?\n"
            "- Who owns sequence control, accountability, and release criteria?\n"
            "- What would embarrass the unit if it went unverified?\n"
            "- What needs rehearsal instead of a verbal assumption?\n\n"
            "Recommended next action:\n"
            "- Write the troop-flow checklist, formation/transition matrix, and leader touchpoint plan now.\n"
            "- Make sequence, accountability method, uniform standard, and speaking or movement order explicit.\n"
            "- Verify ceremony and protocol questions against the governing reference before execution."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role in {"doc", "surgeon"}:
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- If casualty movement, qualified coverage, and stop-training criteria are vague,\n"
            "  the medical plan is not real.\n"
            "- Medical optimism is still risk, even when everyone means well.\n"
            "- The hard question is not whether a template exists;\n"
            "  it is whether the team can execute it under stress.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What casualty scenario is most plausible enough to drive planning?\n"
            "- Who is qualified, equipped, and empowered to make the first hard call?\n"
            "- What TCCC knowledge, trauma-gear familiarity, and first-response\n"
            "  expectations need refresh before execution?\n"
            "- What 9-line, CASEVAC / MEDEVAC, and casualty-collection elements actually need rehearsal here?\n"
            "- What assumption about transport, terrain, comm, or time to higher care is still weak?\n\n"
            "Recommended next action:\n"
            "- Write the casualty scenarios, CASEVAC / MEDEVAC check, casualty collection logic,\n"
            "  coordination triggers, movement assumptions, and stop-training criteria now.\n"
            "- Pause for qualified medical review before pretending the plan is executable."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "g9":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- External coordination fails when the staff treats continuity like a courtesy instead of a requirement.\n"
            "- The team does not need broad theory;\n"
            "  it needs a clean understanding of which outside relationship matters and why.\n"
            "- Civil context helps only if it changes a real command problem, not because it sounds sophisticated.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What civil or partner factor actually changes the plan?\n"
            "- Who owns the next external touchpoint or continuity note?\n"
            "- What assumption about local familiarity or partner access is too casual?\n"
            "- What should be preserved between drills so the unit does not restart from zero?\n\n"
            "Recommended next action:\n"
            "- Narrow the civil picture to the handful of partner and continuity issues that can affect execution.\n"
            "- Write the revalidation point and the owner before drill ends."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role in {"airo", "ace", "wing_ops", "hqmc_aviation"}:
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Start with the supported effect, not the aircraft wish list.\n"
            "- Air-ground integration becomes fragile when airspace, control, comm, fires, safety, and timelines "
            "are handled as separate conversations.\n"
            "- Keep real-world tasking details out of this tool; use this to build the generic staff questions and "
            "coordination products for qualified aviation review.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What aviation effect supports the exercise objective or commander decision?\n"
            "- What airspace, fires, comm, range-control, and safety deconfliction must be solved first?\n"
            "- What request, approval, or support relationship has the longest lead time?\n"
            "- What no-go condition should stop the aviation portion before it creates false training value?\n\n"
            "Recommended next action:\n"
            "- Build an air support estimate with supported effect, control method, comm/PACE, deconfliction "
            "questions, required approvals, and branch/no-go criteria.\n"
            "- Put the AirO, S-3, fires, S-6, safety, and supported GCE/LCE reps in the same coordination matrix."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "sja":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Legal review is useful early; late legal review only tells the commander which avoidable problem has "
            "already become expensive.\n"
            "- Treat this as issue-spotting, not legal advice. Real facts, real people, real investigations, or real "
            "disciplinary action need the proper SJA channel.\n"
            "- Exercise plans still need guardrails: ROE/RUF training injects, safety investigation boundaries, "
            "claims, media release, detainee role-play, and ethics all need clean lanes.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What decision, authority, or legal review trigger is being assumed?\n"
            "- Does the exercise include role-play detainees, escalation-of-force, investigations, claims, imagery, "
            "or public-release issues?\n"
            "- What should commanders, controllers, and evaluators say or avoid saying to prevent confusion?\n"
            "- Where does the plan need SJA review before it is briefed as executable?\n\n"
            "Recommended next action:\n"
            "- Build a legal issue-spotter with ROE/RUF training guardrails, investigation boundaries, claims/release "
            "checks, and a named SJA review point.\n"
            "- Separate training inject fiction from real-world legal authorities and reporting requirements."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role in {"pao", "commstrat", "g7", "hqmc_information"}:
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Public posture is part of the plan, not garnish after the CONOP is done.\n"
            "- OPSEC, release authority, imagery, media access, and the exercise narrative need one coherent owner "
            "and one approval path.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What can be said publicly, by whom, and at what release point?\n"
            "- What imagery, visitor, media, or community touchpoint creates OPSEC or reputation risk?\n"
            "- What message should the exercise reinforce, and what accidental message might it send?\n"
            "- How does PAO/COMMSTRAT coordinate with S-2, S-3, S-6, SJA, and G-9 before release?\n\n"
            "Recommended next action:\n"
            "- Build a public affairs/COMMSTRAT package covering release authority, OPSEC review, imagery handling, "
            "visitor/media choreography, themes and messages, and response-to-query lines."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "safety":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- ORM is not a signature block; it is how the commander decides what risk is worth taking.\n"
            "- A realistic exercise plan needs hazards, controls, residual risk, risk owner, and stop-training "
            "criteria in plain language.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What hazard is most likely, and what hazard is most severe?\n"
            "- Who has authority to stop, pause, or modify training?\n"
            "- What residual risk needs command acceptance instead of staff optimism?\n"
            "- What rehearsal proves the control measure is executable?\n\n"
            "Recommended next action:\n"
            "- Build the ORM worksheet, no-go criteria, residual-risk decision note, and rehearsal safety brief "
            "before the event timeline hardens."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "provost":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Access, force protection, traffic flow, visitor control, and simulated detainee/security injects need "
            "clear boundaries before they touch execution.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What access-control, traffic, or force-protection friction can delay the exercise?\n"
            "- Are any detainee, search, law-enforcement, or security injects fictional and clearly bounded?\n"
            "- What installation or local security coordination must happen before movement?\n"
            "- What needs SJA or safety review because it crosses into authority or risk questions?\n\n"
            "Recommended next action:\n"
            "- Build a security annex with access-control, movement-control, traffic/parking control, visitor "
            "processing, force-protection, emergency action, and SJA/safety coordination points."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role in {"chaplain", "rp"}:
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- Religious support and morale planning are real readiness concerns, especially when the exercise has "
            "casualty, hardship, memorial, or ethical-climate injects.\n"
            "- Preserve confidential support boundaries. The staff can plan support access without exposing private "
            "communications.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- How will Marines access religious, moral, or confidential support during the event?\n"
            "- What casualty, memorial, family, or high-stress scenario needs RMT coordination?\n"
            "- What should be reported as readiness or morale context without exposing confidential communications?\n"
            "- What space, movement, schedule, and security support does the RMT need?\n\n"
            "Recommended next action:\n"
            "- Build the religious support plan, RMT movement/support checklist, morale estimate, and confidentiality "
            "boundary note."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "g8":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- G-8 matters when the plan outruns the money, authorities, or execution window.\n"
            "- The useful output here is not abstract budgeting language; it is a clear tradeoff frame the "
            "commander or XO can actually use.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What resource assumption is carrying too much of the plan?\n"
            "- What can be funded, what can be absorbed, and what needs to be cut or deferred?\n"
            "- What control, audit, or stewardship issue changes the recommendation?\n"
            "- What resourcing decision belongs to command rather than staying buried in staff churn?\n\n"
            "Recommended next action:\n"
            "- Build a resource estimate, priority tradeoff brief, and resourcing decision point with explicit "
            "owners, limits, and next review window."
            f"{active_context_note}"
            f"{osint_note}"
        )

    if definition.role == "ig":
        return (
            f"{definition.title} staff-vetting perspective.\n\n"
            f"Scope: {definition.scope}\n\n"
            "My read:\n"
            "- IG value comes from impartiality. Do not turn this lane into a shortcut for command-directed "
            "investigation or staff enforcement.\n"
            "- For exercises, the useful IG contribution is inspection readiness, compliance trends, complaint "
            "boundaries, and systemic friction.\n\n"
            "Primary lenses:\n"
            f"{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What readiness or compliance issue is systemic rather than merely inconvenient?\n"
            "- Is the staff trying to use IG language for something that belongs to command, SJA, or safety?\n"
            "- What inspection or inquiry boundary must be protected?\n"
            "- What trend should be briefed to the commander without compromising impartiality?\n\n"
            "Recommended next action:\n"
            "- Build an inspection readiness plan, inquiry boundary note, and readiness trend memo; route actual "
            "complaints through proper IG channels."
            f"{active_context_note}"
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
        f"{active_context_note}"
        f"{osint_note}"
    )


def _role_references(role: str) -> tuple[SourceRef, ...]:
    mapping = {
        "xo": S3_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "chief": STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "battle_captain": STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "opso": S3_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "s3": S3_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "s1": S1_REFERENCES,
        "s2": S2_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "g2": S2_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "s4": S4_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "g4": S4_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "s6": S6_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "g6": S6_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "firstsgt": SEL_REFERENCES,
        "sgtmaj": SEL_REFERENCES,
        "doc": MEDICAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "surgeon": MEDICAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "g9": G9_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "g7": PAO_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "g8": G8_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "meu_s3": S3_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "meu_s4": S4_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "blt": S3_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "ace": S3_REFERENCES + ORM_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "airo": S3_REFERENCES + ORM_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "lce": S4_REFERENCES + MEDICAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "wing_ops": S3_REFERENCES + ORM_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "mlg_log": S4_REFERENCES + MEDICAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "sja": LEGAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "pao": PAO_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "commstrat": PAO_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "ig": IG_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "chaplain": LEADERSHIP_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "rp": LEADERSHIP_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "safety": ORM_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "provost": FORCE_PROTECTION_REFERENCES + LEGAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "hqmc_mra": S1_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "hqmc_ppo": S3_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "hqmc_pr": STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "hqmc_il": S4_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "hqmc_aviation": S3_REFERENCES + ORM_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "hqmc_information": STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "hqmc_cdi": S3_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
    }
    return mapping.get(role, ())
