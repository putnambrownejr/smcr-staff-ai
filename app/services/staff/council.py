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
            perspectives.append(
                StaffPerspective(
                    agent_id=role.agent_id,
                    role=role.role,
                    echelon=role.echelon,
                    answer=response.answer,
                    concerns=_extract_section(response.answer, "Concerns to test:"),
                    recommendations=_extract_section(response.answer, "Recommended next action:"),
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
        echelons = request.echelons or [StaffEchelon.company, StaffEchelon.battalion, StaffEchelon.division_group]
        councils = [
            self.vet_idea(
                StaffCouncilRequest(
                    question=request.question,
                    echelon=echelon,
                    roles=request.roles,
                    context={**request.context, "round_robin_phase": "initial_estimate"},
                )
            )
            for echelon in echelons
        ]
        return StaffRoundRobinResponse(
            question=request.question,
            phases=["initial_estimate", "critique", "cross_staff_risks", "synthesis"],
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
    }
    return aliases.get(value, value)
