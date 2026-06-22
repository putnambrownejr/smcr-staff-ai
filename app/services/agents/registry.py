from collections.abc import Iterable

import yaml

from app.schemas.agents import AgentMetadata
from app.services.agents.artillery_08xx_agent import build_artillery_08xx_agent
from app.services.agents.assessment_learning_agent import build_assessment_learning_agent
from app.services.agents.base import Agent
from app.services.agents.chief_of_staff_agent import build_chief_of_staff_agent
from app.services.agents.drill_prep_agent import build_drill_prep_agent
from app.services.agents.infantry_03xx_agent import build_infantry_03xx_agent
from app.services.agents.installation_agent import build_installation_agent
from app.services.agents.leadership_agent import build_leadership_agent
from app.services.agents.map_agent import build_map_agent
from app.services.agents.orm_agent import build_orm_agent
from app.services.agents.osint_agent import build_osint_agent
from app.services.agents.pki_agent import build_pki_troubleshooter_agent
from app.services.agents.planning_advisor_agent import build_planning_advisor_agent
from app.services.agents.privacy_hygiene_agent import build_privacy_hygiene_agent
from app.services.agents.red_team_agent import build_red_team_agent
from app.services.agents.staff_advisor_agent import build_staff_advisor_agents
from app.services.agents.staff_products_agent import build_staff_products_agent
from app.services.agents.uniform_agent import build_uniform_agent
from app.services.agents.writing_briefing_agent import build_writing_briefing_agent


class AgentRegistry:
    def __init__(self, agents: Iterable[Agent] | None = None) -> None:
        self._agents: dict[str, Agent] = {}
        for agent in agents or default_agents():
            self.register(agent)

    def register(self, agent: Agent) -> None:
        self._agents[agent.metadata.id] = agent

    def get(self, agent_id: str) -> Agent | None:
        return self._agents.get(agent_id)

    def list_metadata(self) -> list[AgentMetadata]:
        return [agent.metadata for agent in self._agents.values()]

    @classmethod
    def from_yaml(cls, path: str) -> "AgentRegistry":
        with open(path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        agents: list[Agent] = default_agents()
        configured_ids = {entry["id"] for entry in payload.get("agents", []) if "id" in entry}
        registry = cls(agent for agent in agents if agent.metadata.id in configured_ids or not configured_ids)
        return registry


def default_agents() -> list[Agent]:
    return [
        # Standalone utility agents
        build_chief_of_staff_agent(),
        build_planning_advisor_agent(),
        build_red_team_agent(),
        build_assessment_learning_agent(),
        build_writing_briefing_agent(),
        build_uniform_agent(),
        build_drill_prep_agent(),
        build_staff_products_agent(),
        build_orm_agent(),
        build_installation_agent(),
        build_infantry_03xx_agent(),
        build_artillery_08xx_agent(),
        build_pki_troubleshooter_agent(),
        build_privacy_hygiene_agent(),
        build_leadership_agent(),
        build_osint_agent(),
        build_map_agent(),
        # Consolidated staff archetypes (echelon-adaptive, MOS depth merged in)
        *build_staff_advisor_agents(),
    ]


agent_registry = AgentRegistry()
