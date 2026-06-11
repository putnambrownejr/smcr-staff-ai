from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import (
    StaffCouncilRequest,
    StaffCouncilResponse,
    StaffEchelon,
    StaffPerspective,
    StaffRoleMetadata,
    StaffRoundRobinRequest,
    StaffRoundRobinResponse,
)
from app.services.agents.base import AgentContext
from app.services.agents.staff_advisor_agent import build_staff_advisor_agents, list_staff_role_metadata


class StaffCouncilService:
    def __init__(self) -> None:
        self._agents = {agent.metadata.id: agent for agent in build_staff_advisor_agents()}
        self._roles = list_staff_role_metadata()

    def roles(self) -> list[StaffRoleMetadata]:
        return self._roles

    def vet_idea(self, request: StaffCouncilRequest) -> StaffCouncilResponse:
        selected_roles = {_normalize_role(role) for role in request.roles}
        available_roles = {role.role for role in self._roles if role.echelon == request.echelon}
        roles_missing = sorted(selected_roles - available_roles)
        if roles_missing:
            raise ValueError(f"Unknown roles for {request.echelon.value}: {', '.join(roles_missing)}")
        g9_relevant = _is_g9_relevant(request.question, request.context)
        candidates = [
            role
            for role in self._roles
            if role.echelon == request.echelon
            and (not selected_roles or role.role in selected_roles)
            and (selected_roles or role.role != "g9" or g9_relevant)
        ]
        context = AgentContext(extra=request.context)
        perspectives: list[StaffPerspective] = []
        for role in candidates:
            agent = self._agents[role.agent_id]
            response = agent.run(request.question, context)
            definition = agent.definition
            phase = str(request.context.get("round_robin_phase", "section_estimate"))
            perspectives.append(
                StaffPerspective(
                    agent_id=role.agent_id,
                    role=role.role,
                    echelon=role.echelon,
                    phase=phase,
                    magtf_lenses=list(definition.magtf_lenses),
                    answer=response.answer,
                    estimate=_build_estimate(role.role, definition.focus, request.question),
                    critical_questions=_build_critical_questions(role.role),
                    assumptions_to_test=_build_assumptions(role.role),
                    concerns=_extract_section(response.answer, "Concerns to test:"),
                    critique_points=_build_critique_points(role.role),
                    cross_staff_risks=_build_cross_staff_risks(role.role),
                    recommendations=_extract_section(response.answer, "Recommended next action:"),
                    recommended_products=list(definition.products) or _default_products(role.role),
                    coordination_notes=_build_coordination_notes(role.role),
                    branch_sequel_prompts=_build_branch_prompts(role.role),
                    commander_decisions=_build_commander_decisions(role.role),
                    mcpp_step=_mcpp_step_for_phase(phase),
                    mcpp_discipline=_mcpp_discipline_for_role(role.role),
                    pme_grounding=(
                        "EWS/C&S-style staff work: state assumptions, build estimates, critique across functions, "
                        "surface friction, and force commander decisions."
                    ),
                    citations=response.citations,
                    structured_citations=[citation.model_dump() for citation in response.structured_citations],
                    action_items=_extract_section(response.answer, "Recommended next action:"),
                    assumptions=["Reserve time, personnel availability, and official guidance must be verified."],
                    confidence=response.confidence.value,
                )
            )
        synthesis = _build_council_synthesis(perspectives)
        return StaffCouncilResponse(
            question=request.question,
            echelon=request.echelon,
            perspectives=perspectives,
            synthesis=synthesis,
            roles_requested=request.roles,
            roles_run=[role.role for role in candidates],
            roles_missing=roles_missing,
            warnings=[
                *DEFAULT_WARNINGS,
                "Staff council output is advisory and does not represent official command guidance.",
            ],
        )

    def round_robin(self, request: StaffRoundRobinRequest) -> StaffRoundRobinResponse:
        echelons = request.echelons or [
            StaffEchelon.company,
            StaffEchelon.battalion,
            StaffEchelon.regiment_meu_wing,
            StaffEchelon.division_group,
        ]
        phases = ["section_estimates", "critique_other_sections", "cross_staff_friction", "commander_xo_synthesis"]
        councils: list[StaffCouncilResponse] = []
        for phase in phases:
            for echelon in echelons:
                phase_roles = request.roles
                if request.roles:
                    available_roles = {role.role for role in self._roles if role.echelon == echelon}
                    phase_roles = [
                        role for role in {_normalize_role(role) for role in request.roles} if role in available_roles
                    ]
                    if not phase_roles:
                        continue
                councils.append(
                    self.vet_idea(
                        StaffCouncilRequest(
                            question=request.question,
                            echelon=echelon,
                            roles=phase_roles,
                            context={**request.context, "round_robin_phase": phase},
                        )
                    )
                )
        return StaffRoundRobinResponse(
            question=request.question,
            phases=phases,
            councils=councils,
            synthesis=_build_round_robin_synthesis(councils),
            warnings=[
                *DEFAULT_WARNINGS,
                "Round robin is an advisory staff simulation, not command guidance or an order.",
            ],
        )


def _is_g9_relevant(question: str, context: dict[str, object]) -> bool:
    keyword_text = " ".join(
        [
            question,
            " ".join(str(value) for value in context.values() if value is not None),
        ]
    ).lower()
    relevance_terms = {
        "civil",
        "civilian",
        "community",
        "partner",
        "ngo",
        "interagency",
        "humanitarian",
        "disaster",
        "local authority",
        "population",
        "external coordination",
        "engagement",
        "key leader",
        "cmo",
        "ca ",
        "civil affairs",
    }
    return any(term in keyword_text for term in relevance_terms)


def _extract_section(answer: str, marker: str) -> list[str]:
    if marker not in answer:
        return []
    tail = answer.split(marker, maxsplit=1)[1]
    lines = [line.strip("- ").strip() for line in tail.splitlines() if line.strip().startswith("-")]
    return lines[:4]


def _build_council_synthesis(perspectives: list[StaffPerspective]) -> str:
    if not perspectives:
        return "No staff perspectives ran. Confirm the right roles and restate the problem more clearly."

    roles = ", ".join(p.role.upper() for p in perspectives[:4])
    first_concern = next((item for p in perspectives for item in p.concerns if item), None)
    first_recommendation = next((item for p in perspectives for item in p.recommendations if item), None)
    synthesis = (
        f"Staff view from {roles}: do not confuse a well-organized draft for an executable plan. "
        "The next move is to resolve the first real friction point, assign the owner, and force a command decision "
        "where assumptions are still carrying too much weight."
    )
    if first_concern:
        synthesis += f" First friction to settle: {first_concern}"
    if first_recommendation:
        synthesis += f" Best immediate move: {first_recommendation}"
    return synthesis


def _build_round_robin_synthesis(councils: list[StaffCouncilResponse]) -> str:
    concerns = [item for council in councils for perspective in council.perspectives for item in perspective.concerns]
    recommendations = [
        item for council in councils for perspective in council.perspectives for item in perspective.recommendations
    ]
    synthesis = (
        "Round robin complete. Treat this like a real staff fight, not a stack of polite comments: identify the "
        "assumption that will break execution first, cut what cannot be resourced, assign owners, and verify every "
        "important claim against official sources or user-confirmed local context before action."
    )
    if concerns:
        synthesis += f" First cross-staff friction: {concerns[0]}"
    if recommendations:
        synthesis += f" First action to drive: {recommendations[0]}"
    return synthesis


def _build_estimate(role: str, focus: tuple[str, ...], question: str) -> list[str]:
    return [
        f"Frame the problem for the {role.upper()} lane: {question}",
        "Convert the concept into assumptions, constraints, support requirements, and decision points.",
        *(f"Estimate focus: {item}." for item in focus[:3]),
    ][:5]


def _build_critical_questions(role: str) -> list[str]:
    special = {
        "airo": [
            "What supported aviation effect is required?",
            "What airspace, control, fires, comm, and safety deconfliction is unresolved?",
            "Who is the qualified aviation reviewer and when do they review the plan?",
        ],
        "sja": [
            "What legal authority, review trigger, or ROE/RUF assumption is being used?",
            "Does the exercise include investigations, claims, public release, detainee role-play, "
            "or force escalation?",
            "What must move to the proper SJA channel before action?",
        ],
        "pao": [
            "What is releasable, who can release it, and when?",
            "What imagery, media, visitor, or community touchpoint creates OPSEC risk?",
            "What response-to-query line is needed before execution?",
        ],
        "commstrat": [
            "What public impact could the plan create?",
            "What message should the exercise reinforce?",
            "How do PAO, S-2, S-3, S-6, SJA, and G-9 synchronize information actions?",
        ],
        "g8": [
            "What resource or funding assumption is most likely to break first?",
            "What should be cut, deferred, or rephased if full resourcing is not available?",
            "What resourcing decision belongs to command instead of staying at staff level?",
        ],
        "safety": [
            "What is the most likely hazard and the most severe hazard?",
            "Who accepts residual risk?",
            "Who can stop or modify training?",
        ],
        "provost": [
            "What access-control, traffic, or force-protection issue can delay execution?",
            "What security injects require SJA or safety review?",
            "What installation or local security coordination is required?",
        ],
        "chaplain": [
            "How will Marines access religious or confidential support?",
            "What morale, casualty, memorial, or family-support scenario needs RMT planning?",
            "What can be briefed without breaching confidentiality?",
        ],
        "ig": [
            "What issue is systemic enough to affect readiness?",
            "What belongs to IG channels versus command, SJA, or safety channels?",
            "What inquiry or inspection boundary must remain independent?",
        ],
    }
    return special.get(role, ["What decision does this staff lane support?", "What assumption is still unverified?"])


def _build_assumptions(role: str) -> list[str]:
    base = ["Local SOPs, current orders, and qualified human reviewers remain authoritative."]
    if role in {"airo", "ace", "wing_ops"}:
        return [
            *base,
            "Aviation support is hypothetical until approved by qualified aviation reviewers through proper channels.",
        ]
    if role == "sja":
        return [*base, "This is issue-spotting only and not legal advice."]
    if role in {"pao", "commstrat", "g7"}:
        return [*base, "Public release authority and OPSEC review must be verified."]
    if role in {"g8"}:
        return [*base, "Resource availability, fiscal controls, and comptroller review must be verified locally."]
    if role in {"chaplain", "rp"}:
        return [*base, "Confidential communications are not exposed to the staff estimate."]
    if role == "ig":
        return [*base, "IG independence, complaint routing, and inspection authorities must remain protected."]
    return base


def _build_critique_points(role: str) -> list[str]:
    return [
        f"Challenge whether the {role.upper()} lane has a real owner and suspense.",
        "Challenge whether the product can be built inside the reserve planning timeline.",
        "Challenge whether another staff section must approve or review before execution.",
    ]


def _build_cross_staff_risks(role: str) -> list[str]:
    mapping = {
        "airo": ["AirO/S-3/S-6/safety/fires deconfliction is late or fragmented."],
        "sja": ["Legal review is delayed until after the plan has already shaped behavior."],
        "pao": ["Public affairs, OPSEC, SJA, and G-9 tell different stories externally."],
        "commstrat": ["Information effects are detached from the actual scheme of maneuver."],
        "g8": ["The staff builds a plan whose cost, lead time, or controls were never tested honestly."],
        "safety": ["ORM exists as a form but not as command-owned risk acceptance."],
        "provost": ["Access control or force protection blocks movement after the schedule hardens."],
        "chaplain": ["Support access is planned too late for high-stress or casualty injects."],
        "ig": ["The staff confuses IG independence with command-tasking convenience."],
    }
    return mapping.get(role, ["A dependency crosses staff boundaries without a named owner."])


def _default_products(role: str) -> list[str]:
    return [f"{role.upper()} estimate", "coordination checklist", "commander decision point"]


def _build_coordination_notes(role: str) -> list[str]:
    mapping = {
        "airo": ["Coordinate with S-3, fires, S-6, safety, ACE, GCE, LCE, and range/control authorities."],
        "sja": ["Coordinate with commander/XO, S-3, PAO/COMMSTRAT, safety, provost, and IG as applicable."],
        "pao": ["Coordinate with S-2, S-3, S-6, SJA, COMMSTRAT, G-9, and release authority."],
        "g8": ["Coordinate with commander/XO, S-3, S-4, S-1, and comptroller/resource reviewers as applicable."],
        "safety": ["Coordinate with S-3, S-4, medical, AirO/ACE, range control, and the risk-acceptance authority."],
        "provost": ["Coordinate with S-2, S-3, S-4, SJA, safety, installation access, and local security partners."],
        "chaplain": ["Coordinate with commander, S-1, medical, RP, PAO for public ceremonies, and SJA for boundaries."],
        "ig": ["Coordinate carefully with commander and SJA while preserving IG independence."],
    }
    return mapping.get(role, ["Coordinate with adjacent staff sections before briefing the plan as executable."])


def _build_branch_prompts(role: str) -> list[str]:
    return [
        f"What branch is required if the {role.upper()} assumption fails?",
        "What sequel preserves training value if the preferred plan is not supportable?",
    ]


def _build_commander_decisions(role: str) -> list[str]:
    if role == "safety":
        return ["Accept, reduce, transfer, or reject residual risk."]
    if role == "airo":
        return ["Approve the desired aviation effect, control method, and no-go criteria for planning."]
    if role == "sja":
        return ["Direct formal SJA review before the plan is briefed as executable."]
    if role == "g8":
        return ["Approve the cut, defer, fund, or rephase decision before the staff overpromises execution."]
    return ["Assign owner, suspense, and review authority for this lane."]


def _mcpp_step_for_phase(phase: str) -> str:
    mapping = {
        "section_estimates": "problem framing / mission analysis",
        "critique_other_sections": "COA development and staff estimates",
        "cross_staff_friction": "COA wargaming / comparison",
        "commander_xo_synthesis": "decision and transition",
    }
    return mapping.get(phase, "staff estimate")


def _mcpp_discipline_for_role(role: str) -> str:
    if role in {"s3", "opso", "meu_s3", "g3"}:
        return "Tie the event to objectives, standards, timeline, assessment, and AAR."
    if role in {"airo", "ace", "wing_ops"}:
        return "State supported aviation effect, control method, deconfliction, and qualified-review needs."
    if role == "sja":
        return "Issue-spot authorities, review triggers, and boundaries before execution."
    if role in {"pao", "commstrat", "g7"}:
        return "Connect public posture, OPSEC, release authority, and information effects."
    if role in {"g8"}:
        return "Translate resource posture into command tradeoffs, controls, and decisions."
    if role == "ig":
        return "Protect inquiry boundaries while surfacing readiness trends and inspection friction."
    return "Maintain a running estimate with assumptions, risks, coordination, and decision points."


def _normalize_role(role: str) -> str:
    value = role.lower().replace("-", "").replace(" ", "")
    aliases = {
        "1stsgt": "firstsgt",
        "firstsergeant": "firstsgt",
        "companygunnerysergeant": "cogysgt",
        "cogunny": "cogysgt",
        "corpsman": "doc",
        "medicalofficer": "surgeon",
        "medicalplanner": "surgeon",
        "doc": "doc",
        "battalionsurgeon": "surgeon",
        "s3": "s3",
        "opso": "opso",
        "operationsofficer": "opso",
        "airofficer": "airo",
        "airo": "airo",
        "air": "airo",
        "jag": "sja",
        "legal": "sja",
        "legalofficer": "sja",
        "publicaffairs": "pao",
        "publicaffairsofficer": "pao",
        "pa": "pao",
        "communicationstrategy": "commstrat",
        "comstrat": "commstrat",
        "information": "commstrat",
        "safetyofficer": "safety",
        "provostmarshal": "provost",
        "mp": "provost",
        "militarypolice": "provost",
        "religiousprogramspecialist": "rp",
        "inspector": "ig",
        "inspectorgeneral": "ig",
    }
    return aliases.get(value, value)
