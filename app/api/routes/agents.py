from collections.abc import Iterator
from typing import Annotated

from app.core.auth import LocalApiKeyDependency
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.schemas.agents import AgentMetadata, AgentRunRequest, AgentRunResponse
from app.services.agents.base import AgentContext
from app.services.agents.registry import agent_registry
from app.services.session.active_context_store import ActiveUserContextStore

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[LocalApiKeyDependency])


def get_active_context_store() -> Iterator[ActiveUserContextStore]:
    settings = get_settings()
    yield ActiveUserContextStore(f"{settings.local_context_storage_dir}/active_user_context")


@router.get("", response_model=list[AgentMetadata])
def list_agents() -> list[AgentMetadata]:
    return agent_registry.list_metadata()


@router.post("/{agent_id}/run", response_model=AgentRunResponse)
def run_agent(
    agent_id: str,
    request: AgentRunRequest,
    active_context_store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
) -> AgentRunResponse:
    agent = agent_registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    context_payload = dict(request.context)
    if user_key := context_payload.get("user_key"):
        stored_context = active_context_store.get(str(user_key))
        if stored_context is not None:
            extra = dict(context_payload.get("extra") or {})
            extra["active_user_context"] = stored_context.model_dump(mode="json")
            context_payload["extra"] = extra
    known_keys = {"user_key", "user_role", "unit_id", "request_is_training_or_fictional", "extra"}
    unknown_context = {key: value for key, value in context_payload.items() if key not in known_keys}
    if unknown_context:
        extra = dict(context_payload.get("extra") or {})
        extra.update(unknown_context)
        context_payload["extra"] = extra
    context = AgentContext.model_validate(context_payload)
    return agent.run(request.input, context)
