from collections.abc import Iterable

import yaml

from app.schemas.agents import AgentMetadata
from app.services.agents.admin_agent import build_admin_readiness_agent
from app.services.agents.airo_agent import build_airo_agent
from app.services.agents.base import Agent
from app.services.agents.chaplain_agent import build_chaplain_agent
from app.services.agents.chief_of_staff_agent import build_chief_of_staff_agent
from app.services.agents.correspondence_agent import build_correspondence_formatting_agent
from app.services.agents.drill_prep_agent import build_drill_prep_agent
from app.services.agents.fitrep_agent import build_fitrep_agent
from app.services.agents.g9_civil_military_agent import build_g9_civil_military_agent
from app.services.agents.installation_agent import build_installation_agent
from app.services.agents.jag_agent import build_jag_agent
from app.services.agents.leadership_agent import build_leadership_agent
from app.services.agents.map_agent import build_map_agent
from app.services.agents.maradmin_agent import build_maradmin_agent
from app.services.agents.mcpp_agent import build_mcpp_agent
from app.services.agents.medical_doc_agent import build_medical_doc_agent
from app.services.agents.mos_civil_affairs_agent import build_mos_civil_affairs_agent
from app.services.agents.mos_commo_agent import build_mos_commo_agent
from app.services.agents.opord_agent import build_opord_agent
from app.services.agents.orm_agent import build_orm_agent
from app.services.agents.osint_agent import build_osint_agent
from app.services.agents.pki_agent import build_pki_troubleshooter_agent
from app.services.agents.privacy_hygiene_agent import build_privacy_hygiene_agent
from app.services.agents.r2p2_agent import build_r2p2_agent
from app.services.agents.s1_admin_chief_agent import build_s1_admin_chief_agent
from app.services.agents.s2_intel_agent import build_s2_intel_agent
from app.services.agents.s3_opso_agent import build_s3_opso_agent
from app.services.agents.s4_logistics_agent import build_s4_logistics_agent
from app.services.agents.s6_comms_agent import build_s6_comms_agent
from app.services.agents.sel_enlisted_leader_agent import build_sel_enlisted_leader_agent
from app.services.agents.staff_advisor_agent import build_staff_advisor_agents
from app.services.agents.staff_products_agent import build_staff_products_agent
from app.services.agents.training_agent import build_training_agent
from app.services.agents.uniform_agent import build_uniform_agent


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
        build_admin_readiness_agent(),
        build_airo_agent(),
        build_chaplain_agent(),
        build_s1_admin_chief_agent(),
        build_s2_intel_agent(),
        build_s3_opso_agent(),
        build_s4_logistics_agent(),
        build_s6_comms_agent(),
        build_sel_enlisted_leader_agent(),
        build_chief_of_staff_agent(),
        build_correspondence_formatting_agent(),
        build_maradmin_agent(),
        build_medical_doc_agent(),
        build_mcpp_agent(),
        build_uniform_agent(),
        build_drill_prep_agent(),
        build_opord_agent(),
        build_staff_products_agent(),
        build_training_agent(),
        build_orm_agent(),
        build_fitrep_agent(),
        build_installation_agent(),
        build_g9_civil_military_agent(),
        build_jag_agent(),
        build_pki_troubleshooter_agent(),
        build_privacy_hygiene_agent(),
        build_r2p2_agent(),
        build_leadership_agent(),
        build_osint_agent(),
        build_map_agent(),
        build_mos_commo_agent(),
        build_mos_civil_affairs_agent(),
        *build_staff_advisor_agents(),
    ]


agent_registry = AgentRegistry()
