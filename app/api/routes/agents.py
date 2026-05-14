from fastapi import APIRouter, HTTPException

from app.schemas.agents import AgentMetadata, AgentRunRequest, AgentRunResponse
from app.services.agents.base import AgentContext
from app.services.agents.registry import agent_registry

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentMetadata])
def list_agents() -> list[AgentMetadata]:
    return agent_registry.list_metadata()


@router.post("/{agent_id}/run", response_model=AgentRunResponse)
def run_agent(agent_id: str, request: AgentRunRequest) -> AgentRunResponse:
    agent = agent_registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    context_payload = dict(request.context)
    known_keys = {"user_role", "unit_id", "request_is_training_or_fictional", "extra"}
    unknown_context = {key: value for key, value in context_payload.items() if key not in known_keys}
    if unknown_context:
        extra = dict(context_payload.get("extra") or {})
        extra.update(unknown_context)
        context_payload["extra"] = extra
    context = AgentContext.model_validate(context_payload)
    return agent.run(request.input, context)
