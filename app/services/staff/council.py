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
        candidates = [
            role
            for role in self._roles
            if role.echelon == request.echelon and (not selected_roles or role.role in selected_roles)
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
        synthesis = (
            "Use these perspectives as a staff sanity check. Resolve conflicting assumptions, assign owners, "
            "identify official sources to verify, and route final decisions to the appropriate human chain."
        )
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
            synthesis=(
                "Round robin complete. Compare role concerns, identify dissent, assign owners, and verify every "
                "claim against official sources or user-confirmed local context before action."
            ),
            warnings=[
                *DEFAULT_WARNINGS,
                "Round robin is an advisory staff simulation, not command guidance or an order.",
            ],
        )


def _extract_section(answer: str, marker: str) -> list[str]:
    if marker not in answer:
        return []
    tail = answer.split(marker, maxsplit=1)[1]
    lines = [line.strip("- ").strip() for line in tail.splitlines() if line.strip().startswith("-")]
    return lines[:4]


def _normalize_role(role: str) -> str:
    value = role.lower().replace("-", "").replace(" ", "")
    aliases = {
        "1stsgt": "firstsgt",
        "firstsergeant": "firstsgt",
        "companygunnerysergeant": "cogysgt",
        "cogunny": "cogysgt",
        "s3": "s3",
        "opso": "opso",
        "operationsofficer": "opso",
    }
    return aliases.get(value, value)
