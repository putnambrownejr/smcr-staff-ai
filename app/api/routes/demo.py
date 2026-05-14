from fastapi import APIRouter, HTTPException

from app.schemas.agents import AgentRunRequest, AgentRunResponse
from app.schemas.analysis import TextAnalysisRequest, TextAnalysisResponse
from app.schemas.career import CareerWatchResponse
from app.schemas.chief import ChiefBriefResponse
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductDraftResponse
from app.services.agents.base import AgentContext
from app.services.agents.registry import agent_registry
from app.services.analysis.summarizer import TextAnalysisService
from app.services.demo.scenarios import DEMO_USER_KEY, build_demo_career_watch, build_demo_chief_brief
from app.services.staff_products.builder import StaffProductBuilder

router = APIRouter(prefix="/demo", tags=["demo"])
_analysis_service = TextAnalysisService()
_staff_product_builder = StaffProductBuilder()


@router.get("/status", summary="Show repo-mode demo capabilities")
def demo_status() -> dict[str, object]:
    return {
        "mode": "stateless_demo",
        "user_key": DEMO_USER_KEY,
        "notes": [
            "Demo routes do not depend on user-local storage or prior setup.",
            "They exist to make the repository easier to understand from GitHub and OpenAPI alone.",
            "Private/local workflows still require the non-demo routes and local context storage.",
        ],
        "routes": [
            "/demo/status",
            "/demo/chief/brief",
            "/demo/career/watch",
            "/demo/analysis/summarize",
            "/demo/staff-products/draft",
            "/demo/agents/{agent_id}/run",
        ],
    }


@router.get("/chief/brief", response_model=ChiefBriefResponse, summary="Get a stateless demo Chief/Aide brief")
def demo_chief_brief() -> ChiefBriefResponse:
    return build_demo_chief_brief()


@router.get("/career/watch", response_model=CareerWatchResponse, summary="Get a stateless demo career watch")
def demo_career_watch() -> CareerWatchResponse:
    return build_demo_career_watch()


@router.post(
    "/analysis/summarize",
    response_model=TextAnalysisResponse,
    summary="Run stateless demo text analysis",
)
def demo_summarize_text(request: TextAnalysisRequest) -> TextAnalysisResponse:
    return _analysis_service.analyze(request)


@router.post(
    "/staff-products/draft",
    response_model=StaffProductDraftResponse,
    summary="Draft a staff product in stateless demo mode",
)
def demo_draft_staff_product(request: StaffProductDraftRequest) -> StaffProductDraftResponse:
    return _staff_product_builder.build(request)


@router.post(
    "/agents/{agent_id}/run",
    response_model=AgentRunResponse,
    summary="Run an agent in stateless demo mode",
)
def demo_run_agent(agent_id: str, request: AgentRunRequest) -> AgentRunResponse:
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
    return agent.run(request.input, AgentContext.model_validate(context_payload))
