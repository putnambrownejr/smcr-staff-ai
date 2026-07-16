from collections.abc import Iterable

import yaml

from app.schemas.agents import AgentMetadata
from app.services.agents.ace_agent import build_ace_agent
from app.services.agents.actor_network_agent import build_actor_network_agent
from app.services.agents.area_study_agent import build_area_study_agent
from app.services.agents.artillery_08xx_agent import build_artillery_08xx_agent
from app.services.agents.assessment_learning_agent import build_assessment_learning_agent
from app.services.agents.base import Agent
from app.services.agents.checkin_agent import build_checkin_agent
from app.services.agents.chief_of_staff_agent import build_chief_of_staff_agent
from app.services.agents.drill_prep_agent import build_drill_prep_agent
from app.services.agents.gce_agent import build_gce_agent
from app.services.agents.infantry_03xx_agent import build_infantry_03xx_agent
from app.services.agents.information_requirements_agent import build_information_requirements_agent
from app.services.agents.installation_agent import build_installation_agent
from app.services.agents.ipb_agent import build_ipb_assistant_agent
from app.services.agents.lce_agent import build_lce_agent
from app.services.agents.leadership_agent import build_leadership_agent
from app.services.agents.map_agent import build_map_agent
from app.services.agents.orm_agent import build_orm_agent
from app.services.agents.osint_agent import build_osint_agent
from app.services.agents.pki_agent import build_pki_troubleshooter_agent
from app.services.agents.planning_advisor_agent import build_planning_advisor_agent
from app.services.agents.readiness_development_agents import (
    build_family_deployment_readiness_agent,
    build_financial_readiness_agent,
    build_fitness_planning_agent,
    build_gtcc_advisor_agent,
    build_warrior_monk_agent,
)
from app.services.agents.red_team_agent import build_red_team_agent
from app.services.agents.staff_advisor_agent import build_staff_advisor_agents
from app.services.agents.staff_products_agent import build_staff_products_agent
from app.services.agents.uniform_agent import build_uniform_agent
from app.services.agents.writing_briefing_agent import build_writing_briefing_agent

# Curated, human-facing groups for the dashboard AI page. Each agent's own
# `domain` stays its fine-grained self-description; this buckets the 30+ agents
# into a handful of categories (several agents each) so the page reads cleanly.
# Any id starting with "staff-" is a virtual staff-council seat (see
# build_staff_advisor_agents) and is grouped together automatically.
_AGENT_CATEGORY_BY_ID: dict[str, str] = {
    "chief-of-staff": "Command & Leadership",
    "leadership-advisor": "Command & Leadership",
    "warrior-monk": "Command & Leadership",
    "drill-prep-calendar": "Command & Leadership",
    "unit-checkin": "Command & Leadership",
    "planning-advisor": "Planning & Decision",
    "red-team-assumptions-challenge": "Planning & Decision",
    "assessment-learning-advisor": "Planning & Decision",
    "staff-products": "Staff Products & Communication",
    "writing-briefing-coach": "Staff Products & Communication",
    "ace": "MAGTF Warfighting Elements",
    "gce": "MAGTF Warfighting Elements",
    "lce": "MAGTF Warfighting Elements",
    "fires-advisor": "MAGTF Warfighting Elements",
    "infantry-tactics-advisor": "MAGTF Warfighting Elements",
    "osint-research-assistant": "Intelligence & Research",
    "terrain-map-advisor": "Intelligence & Research",
    "area-study-builder": "Intelligence & Research",
    "actor-network-analyst": "Intelligence & Research",
    "information-requirements-manager": "Intelligence & Research",
    "ipb-assistant": "Intelligence & Research",
    "pki-cac-troubleshooter": "Reserve Admin & Readiness",
    "uniform-advisor": "Reserve Admin & Readiness",
    "installation-practical-advisor": "Reserve Admin & Readiness",
    "orm-risk-management": "Reserve Admin & Readiness",
    "gtcc-advisor": "Reserve Admin & Readiness",
    "financial-readiness-advisor": "Reserve Admin & Readiness",
    "fitness-planning-advisor": "Reserve Admin & Readiness",
    "family-deployment-readiness-advisor": "Reserve Admin & Readiness",
}
_STAFF_COUNCIL_CATEGORY = "Virtual Staff Council"
# Order categories intentionally so the page leads with the most-used groups.
AGENT_CATEGORY_ORDER: list[str] = [
    "Command & Leadership",
    "Planning & Decision",
    "Staff Products & Communication",
    "Reserve Admin & Readiness",
    "MAGTF Warfighting Elements",
    "Intelligence & Research",
    "Virtual Staff Council",
    "Other Advisors",
]


def category_for_agent(agent_id: str) -> str:
    # Explicit mapping wins first -- "staff-products" starts with "staff-" but is
    # a real staff-product agent, not a virtual staff-council seat.
    if agent_id in _AGENT_CATEGORY_BY_ID:
        return _AGENT_CATEGORY_BY_ID[agent_id]
    if agent_id.startswith("staff-"):
        return _STAFF_COUNCIL_CATEGORY
    return "Other Advisors"


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
        return [
            agent.metadata.model_copy(update={"category": category_for_agent(agent.metadata.id)})
            for agent in self._agents.values()
        ]

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
        build_leadership_agent(),
        build_warrior_monk_agent(),
        build_gtcc_advisor_agent(),
        build_financial_readiness_agent(),
        build_fitness_planning_agent(),
        build_family_deployment_readiness_agent(),
        build_osint_agent(),
        build_map_agent(),
        build_area_study_agent(),
        build_actor_network_agent(),
        build_information_requirements_agent(),
        build_ipb_assistant_agent(),
        build_checkin_agent(),
        # MAGTF element agents (standalone)
        build_ace_agent(),
        build_gce_agent(),
        build_lce_agent(),
        # Consolidated staff archetypes (echelon-adaptive, MOS depth merged in)
        *build_staff_advisor_agents(),
    ]


agent_registry = AgentRegistry()
