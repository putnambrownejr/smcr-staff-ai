from collections.abc import Iterable

import yaml

from app.schemas.agents import AgentMetadata, AgentRunResponse
from app.services.agents.ace_agent import build_ace_agent
from app.services.agents.artillery_08xx_agent import build_artillery_08xx_agent
from app.services.agents.assessment_learning_agent import build_assessment_learning_agent
from app.services.agents.base import Agent, AgentContext
from app.services.agents.checkin_agent import build_checkin_agent
from app.services.agents.chief_of_staff_agent import build_chief_of_staff_agent
from app.services.agents.gce_agent import build_gce_agent
from app.services.agents.infantry_03xx_agent import build_infantry_03xx_agent
from app.services.agents.installation_agent import build_installation_agent
from app.services.agents.leadership_agent import build_leadership_agent
from app.services.agents.map_agent import build_map_agent
from app.services.agents.orm_agent import build_orm_agent
from app.services.agents.osint_agent import build_osint_agent
from app.services.agents.pki_agent import build_pki_troubleshooter_agent
from app.services.agents.planning_advisor_agent import build_planning_advisor_agent
from app.services.agents.readiness_development_agents import (
    build_financial_readiness_agent,
    build_fitness_planning_agent,
    build_gtcc_advisor_agent,
)
from app.services.agents.red_team_agent import build_red_team_agent
from app.services.agents.staff_advisor_agent import build_staff_advisor_agents
from app.services.agents.staff_products_agent import build_staff_products_agent
from app.services.agents.uniform_agent import build_uniform_agent
from app.services.agents.writing_briefing_agent import build_writing_briefing_agent

# Curated, human-facing groups for the dashboard AI page. Each agent's own
# `domain` stays its fine-grained self-description; this buckets the roster
# into a handful of categories (several agents each) so the page reads cleanly.
# Any id starting with "staff-" is a virtual staff-council seat (see
# build_staff_advisor_agents) and is grouped together automatically.
_AGENT_CATEGORY_BY_ID: dict[str, str] = {
    "chief-of-staff": "Command & Leadership",
    "leadership-advisor": "Command & Leadership",
    "unit-checkin": "Command & Leadership",
    "planning-advisor": "Planning & Decision",
    "red-team-assumptions-challenge": "Planning & Decision",
    "assessment-learning-advisor": "Planning & Decision",
    "staff-products": "Staff Products & Communication",
    "writing-briefing-coach": "Staff Products & Communication",
    "ace": "MAGTF Warfighting Elements",
    "gce": "MAGTF Warfighting Elements",
    "fires-advisor": "MAGTF Warfighting Elements",
    "infantry-tactics-advisor": "MAGTF Warfighting Elements",
    "osint-research-assistant": "Intelligence & Research",
    "terrain-map-advisor": "Intelligence & Research",
    "pki-cac-troubleshooter": "Reserve Admin & Readiness",
    "uniform-advisor": "Reserve Admin & Readiness",
    "installation-practical-advisor": "Reserve Admin & Readiness",
    "orm-risk-management": "Reserve Admin & Readiness",
    "gtcc-advisor": "Reserve Admin & Readiness",
    "financial-readiness-advisor": "Reserve Admin & Readiness",
    "fitness-planning-advisor": "Reserve Admin & Readiness",
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

# Agent ids that were merged into a surviving agent as a *mode* (Sep 2026
# review). They no longer appear in the catalog, but `get()` still resolves
# them so saved chains, dashboard presets, seed cadence data, and custom MOS
# recipes keep working. Value: (surviving agent id, mode to force, or None).
MERGED_AGENT_ALIASES: dict[str, tuple[str, str | None]] = {
    "lce": ("staff-s4", "lce"),
    "drill-prep-calendar": ("chief-of-staff", "drill_prep"),
    "warrior-monk": ("leadership-advisor", "reflect"),
    "family-deployment-readiness-advisor": ("staff-s1", "family_readiness"),
    "ipb-assistant": ("staff-s2", "ipb"),
    "information-requirements-manager": ("staff-s2", "information_requirements"),
    "area-study-builder": ("staff-g9", "area_study"),
    "actor-network-analyst": ("staff-g9", "actor_network"),
}


def category_for_agent(agent_id: str) -> str:
    # Explicit mapping wins first -- "staff-products" starts with "staff-" but is
    # a real staff-product agent, not a virtual staff-council seat.
    if agent_id in _AGENT_CATEGORY_BY_ID:
        return _AGENT_CATEGORY_BY_ID[agent_id]
    if agent_id.startswith("staff-"):
        return _STAFF_COUNCIL_CATEGORY
    return "Other Advisors"


class MergedAgentAlias(Agent):
    """Routes a retired agent id to its surviving agent with a fixed mode.

    The wrapper carries the survivor's metadata, so responses report the
    surviving agent id. The forced mode is only applied when the caller did
    not already choose one.
    """

    def __init__(self, target: Agent, mode: str | None) -> None:
        self.metadata = target.metadata
        self._target = target
        self.mode = mode

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        if self.mode:
            raw_options = context.extra.get("agent_options")
            options = dict(raw_options) if isinstance(raw_options, dict) else {}
            options.setdefault("mode", self.mode)
            context = context.model_copy(update={"extra": {**context.extra, "agent_options": options}})
        return self._target.run(input_text, context)


class AgentRegistry:
    def __init__(self, agents: Iterable[Agent] | None = None) -> None:
        self._agents: dict[str, Agent] = {}
        for agent in default_agents() if agents is None else agents:
            self.register(agent)

    def register(self, agent: Agent) -> None:
        self._agents[agent.metadata.id] = agent

    def get(self, agent_id: str) -> Agent | None:
        agent = self._agents.get(agent_id)
        if agent is not None:
            return agent
        alias = MERGED_AGENT_ALIASES.get(agent_id)
        if alias is None:
            return None
        target = self._agents.get(alias[0])
        if target is None:
            return None
        return MergedAgentAlias(target, alias[1])

    def list_metadata(self) -> list[AgentMetadata]:
        return [
            agent.metadata.model_copy(update={"category": category_for_agent(agent.metadata.id)})
            for agent in self._agents.values()
        ]

    @classmethod
    def from_yaml(cls, path: str) -> "AgentRegistry":
        with open(path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        if "agents" not in payload:
            return cls()
        agents: list[Agent] = default_agents()
        configured_ids = {entry["id"] for entry in payload.get("agents", []) if "id" in entry}
        configured_ids = {MERGED_AGENT_ALIASES.get(agent_id, (agent_id, None))[0] for agent_id in configured_ids}
        registry = cls(agent for agent in agents if agent.metadata.id in configured_ids)
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
        build_staff_products_agent(),
        build_orm_agent(),
        build_installation_agent(),
        build_infantry_03xx_agent(),
        build_artillery_08xx_agent(),
        build_pki_troubleshooter_agent(),
        build_leadership_agent(),
        build_gtcc_advisor_agent(),
        build_financial_readiness_agent(),
        build_fitness_planning_agent(),
        build_osint_agent(),
        build_map_agent(),
        build_checkin_agent(),
        # MAGTF element agents (standalone; LCE is a mode of staff-s4)
        build_ace_agent(),
        build_gce_agent(),
        # Consolidated staff archetypes (echelon-adaptive, MOS depth merged in)
        *build_staff_advisor_agents(),
    ]


agent_registry = AgentRegistry()
