from dataclasses import dataclass

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.schemas.staff import StaffEchelon, StaffRoleMetadata
from app.services.agents.base import Agent, AgentContext
from app.services.agents.osint_agent import build_osint_agent
from app.services.agents.source_refs import (
    G9_REFERENCES,
    MEDICAL_REFERENCES,
    S1_REFERENCES,
    S2_REFERENCES,
    S3_REFERENCES,
    S4_REFERENCES,
    S6_REFERENCES,
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
            "- Publish one suspense list with owner, due date, source reference, and command touchpoint.\n"
            "- Separate travel, orders, roster, FitRep, readiness, and awards lanes before they contaminate each other."
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
            "- What 9-line and CASEVAC elements actually need rehearsal here?\n"
            "- What assumption about transport, terrain, comm, or time to higher care is still weak?\n\n"
            "Recommended next action:\n"
            "- Write the casualty scenarios, casualty collection plan,\n"
            "  movement assumptions, and stop-training criteria now.\n"
            "- Pause for qualified medical review before pretending the plan is executable."
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


def _role_references(role: str) -> tuple[SourceRef, ...]:
    mapping = {
        "xo": S3_REFERENCES,
        "opso": S3_REFERENCES,
        "s3": S3_REFERENCES,
        "s1": S1_REFERENCES,
        "s2": S2_REFERENCES,
        "g2": S2_REFERENCES,
        "s4": S4_REFERENCES,
        "g4": S4_REFERENCES,
        "s6": S6_REFERENCES,
        "g6": S6_REFERENCES,
        "doc": MEDICAL_REFERENCES,
        "surgeon": MEDICAL_REFERENCES,
        "g9": G9_REFERENCES,
    }
    return mapping.get(role, ())
