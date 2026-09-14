from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.chief_setup import get_chief_setup_store
from app.api.routes.user_docs import get_user_docs_store
from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.automations import (
    Automation,
    AutomationListResponse,
    AutomationPacketRequest,
    AutomationPacketResponse,
    AutomationResponse,
    AutomationTemplate,
    AutomationUpsertRequest,
)
from app.schemas.user_docs import UserDocCategory, UserDocCreateRequest
from app.services.agents.base import Agent
from app.services.agents.registry import agent_registry
from app.services.agents.staff_advisor_agent import StaffAdvisorAgent
from app.services.agents.staff_call_packet import build_staff_call_packet
from app.services.chief.automation_store import AUTOMATION_TEMPLATES, AutomationStore, build_automation_block
from app.services.chief.setup_store import ChiefSetupStore
from app.services.user_docs.store import UserDocsStore

router = APIRouter(prefix="/automations", tags=["automations"], dependencies=[LocalApiKeyDependency])


def get_automation_store() -> Iterator[AutomationStore]:
    settings = get_settings()
    yield AutomationStore(settings.automations_storage_dir)


def _seat_line(agent_id: str, agent: Agent) -> str:
    target = getattr(agent, "_target", agent)
    if isinstance(target, StaffAdvisorAgent):
        return f"{target.metadata.name} ({agent_id}) — {target.archetype.scope}"
    return f"{target.metadata.name} ({agent_id}) — {target.metadata.description}"


def _resolve_agents(agent_ids: list[str]) -> list[tuple[str, Agent]]:
    seated: list[tuple[str, Agent]] = []
    for agent_id in agent_ids:
        agent = agent_registry.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=422, detail=f"Unknown agent: {agent_id}")
        seated.append((agent_id, agent))
    return seated


def _response(automation: Automation, chief_store: ChiefSetupStore) -> AutomationResponse:
    seated = _resolve_agents(automation.agents)
    block = build_automation_block(
        automation,
        chief_setup=chief_store.get(automation.user_key),
        seat_lines=[_seat_line(agent_id, agent) for agent_id, agent in seated],
    )
    return AutomationResponse(
        automation=automation,
        block=block,
        agent_names=[agent.metadata.name for _, agent in seated],
    )


@router.get("/templates", response_model=list[AutomationTemplate])
def list_templates() -> list[AutomationTemplate]:
    return list(AUTOMATION_TEMPLATES)


@router.get("/{user_key}", response_model=AutomationListResponse)
def list_automations(
    user_key: str,
    store: Annotated[AutomationStore, Depends(get_automation_store)],
    chief_store: Annotated[ChiefSetupStore, Depends(get_chief_setup_store)],
) -> AutomationListResponse:
    return AutomationListResponse(automations=[_response(item, chief_store) for item in store.list_all(user_key)])


@router.post("/{user_key}", response_model=AutomationResponse, status_code=201)
def create_automation(
    user_key: str,
    body: AutomationUpsertRequest,
    store: Annotated[AutomationStore, Depends(get_automation_store)],
    chief_store: Annotated[ChiefSetupStore, Depends(get_chief_setup_store)],
) -> AutomationResponse:
    _resolve_agents(body.agents)
    try:
        automation = store.create(user_key, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _response(automation, chief_store)


@router.put("/{user_key}/{automation_id}", response_model=AutomationResponse)
def update_automation(
    user_key: str,
    automation_id: str,
    body: AutomationUpsertRequest,
    store: Annotated[AutomationStore, Depends(get_automation_store)],
    chief_store: Annotated[ChiefSetupStore, Depends(get_chief_setup_store)],
) -> AutomationResponse:
    _resolve_agents(body.agents)
    try:
        automation = store.update(user_key, automation_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if automation is None:
        raise HTTPException(status_code=404, detail="Automation not found.")
    return _response(automation, chief_store)


@router.delete("/{user_key}/{automation_id}", status_code=204)
def delete_automation(
    user_key: str,
    automation_id: str,
    store: Annotated[AutomationStore, Depends(get_automation_store)],
) -> None:
    if not store.delete(user_key, automation_id):
        raise HTTPException(status_code=404, detail="Automation not found.")


@router.post("/{user_key}/{automation_id}/packet", response_model=AutomationPacketResponse)
def build_automation_packet(
    user_key: str,
    automation_id: str,
    body: AutomationPacketRequest,
    store: Annotated[AutomationStore, Depends(get_automation_store)],
    chief_store: Annotated[ChiefSetupStore, Depends(get_chief_setup_store)],
    docs_store: Annotated[UserDocsStore, Depends(get_user_docs_store)],
) -> AutomationPacketResponse:
    """Wrap one run of the automation (its block + this occurrence's input) into a staff call packet."""
    automation = store.get(user_key, automation_id)
    if automation is None:
        raise HTTPException(status_code=404, detail="Automation not found.")
    rendered = _response(automation, chief_store)
    seated = _resolve_agents(automation.agents)
    packet = build_staff_call_packet(
        scenario=body.input,
        participants=seated,
        synthesizer=None,
        kind="automation",
        label=automation.name,
        include_role_notes=body.include_role_notes,
        preamble=rendered.block,
    )
    saved_doc_id: str | None = None
    if body.save:
        entry = docs_store.create(
            UserDocCategory.generations,
            user_key,
            UserDocCreateRequest(
                title=f"Automation run — {automation.name}",
                body=packet,
                fields={"templateType": "automation_run_packet", "automation_id": automation.id, "participants": automation.agents},
            ),
        )
        saved_doc_id = entry.id
    return AutomationPacketResponse(
        automation_id=automation.id,
        name=automation.name,
        participants=automation.agents,
        participant_names=rendered.agent_names,
        packet_markdown=packet,
        saved_doc_id=saved_doc_id,
        note=(
            "No AI analysis was performed. This packet carries your automation's standing instruction, this run's "
            "input, and the seats' lenses for your own AI to execute."
        ),
    )
