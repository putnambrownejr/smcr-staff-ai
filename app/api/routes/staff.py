from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.admin_workflows import (
    AdminWorkflowDraftRequest,
    AdminWorkflowRequest,
    AdminWorkflowResponse,
    AdminWorkflowType,
)
from app.schemas.agents import AgentRunRequest, AgentRunResponse
from app.schemas.pki import PkiTroubleshootingRequest, PkiTroubleshootingResponse
from app.schemas.staff import (
    CommandCellRequest,
    CommandCellResponse,
    G9PlanningRequest,
    G9PlanningResponse,
    MedicalPlanningRequest,
    MedicalPlanningResponse,
    S1ReadinessRequest,
    S1ReadinessResponse,
    S2EstimateRequest,
    S2EstimateResponse,
    S6PlanRequest,
    S6PlanResponse,
    SafetyPlanningRequest,
    SafetyPlanningResponse,
    SelExecutionRequest,
    SelExecutionResponse,
    StaffCouncilRequest,
    StaffCouncilResponse,
    StaffRoleMetadata,
    StaffRoundRobinRequest,
    StaffRoundRobinResponse,
    XoSyncRequest,
    XoSyncResponse,
)
from app.schemas.staff_updates import (
    AssistedSectionEstimateRequest,
    AssistedSectionEstimatesResponse,
    CpbResponse,
    CubResponse,
    LonePlannerResponse,
    MissionAnalysisResponse,
    PlanningCellResponse,
    RunningEstimateRequest,
    RunningEstimateResponse,
    StaffUpdateCycleResponse,
)
from app.services.admin.pki_support import PkiTroubleshootingService
from app.services.admin.workflow_builder import AdminWorkflowBuilder
from app.services.agents.base import AgentContext
from app.services.agents.osint_agent import build_osint_agent
from app.services.staff.command_cell_planner import CommandCellPlanner
from app.services.staff.council import StaffCouncilService
from app.services.staff.g9_planner import G9Planner
from app.services.staff.medical_planner import MedicalPlanner
from app.services.staff.s1_readiness_planner import S1ReadinessPlanner
from app.services.staff.s2_estimator import S2Estimator
from app.services.staff.s6_planner import S6Planner
from app.services.staff.safety_planner import SafetyPlanner
from app.services.staff.section_memory_store import SectionMemoryStore
from app.services.staff.sel_execution_planner import SelExecutionPlanner
from app.services.staff.update_cycle import StaffUpdateCycleBuilder
from app.services.staff.xo_sync_planner import XoSyncPlanner

router = APIRouter(prefix="/staff", tags=["staff council"], dependencies=[LocalApiKeyDependency])

_service = StaffCouncilService()
_command_cell_planner = CommandCellPlanner()
_g9_planner = G9Planner()
_medical_planner = MedicalPlanner()
_s1_readiness_planner = S1ReadinessPlanner()
_safety_planner = SafetyPlanner()
_s2_estimator = S2Estimator()
_sel_execution_planner = SelExecutionPlanner()
_s6_planner = S6Planner()
_pki_service = PkiTroubleshootingService()
_admin_workflow_builder = AdminWorkflowBuilder()
_osint_agent = build_osint_agent()
_update_cycle = StaffUpdateCycleBuilder()
_xo_sync_planner = XoSyncPlanner()


def get_section_memory_store() -> Iterator[SectionMemoryStore]:
    settings = get_settings()
    yield SectionMemoryStore(settings.section_memory_storage_dir)


@router.get("/roles", response_model=list[StaffRoleMetadata])
def list_staff_roles() -> list[StaffRoleMetadata]:
    return _service.roles()


@router.post("/vet-idea", response_model=StaffCouncilResponse)
def vet_idea(request: StaffCouncilRequest) -> StaffCouncilResponse:
    try:
        return _service.vet_idea(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/round-robin", response_model=StaffRoundRobinResponse)
def round_robin(request: StaffRoundRobinRequest) -> StaffRoundRobinResponse:
    try:
        return _service.round_robin(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/s2-estimate", response_model=S2EstimateResponse)
def build_s2_estimate(request: S2EstimateRequest) -> S2EstimateResponse:
    return _s2_estimator.build(request)


@router.post("/xo-sync", response_model=XoSyncResponse)
def build_xo_sync(request: XoSyncRequest) -> XoSyncResponse:
    return _xo_sync_planner.build(request)


@router.post("/command-cell", response_model=CommandCellResponse)
def build_command_cell(request: CommandCellRequest) -> CommandCellResponse:
    return _command_cell_planner.build(request)


@router.post("/s1-readiness", response_model=S1ReadinessResponse)
def build_s1_readiness(request: S1ReadinessRequest) -> S1ReadinessResponse:
    return _s1_readiness_planner.build(request)


@router.post("/s6-plan", response_model=S6PlanResponse)
def build_s6_plan(request: S6PlanRequest) -> S6PlanResponse:
    return _s6_planner.build(request)


@router.post("/safety-plan", response_model=SafetyPlanningResponse)
def build_safety_plan(request: SafetyPlanningRequest) -> SafetyPlanningResponse:
    return _safety_planner.build(request)


@router.post("/sel-execution", response_model=SelExecutionResponse)
def build_sel_execution(request: SelExecutionRequest) -> SelExecutionResponse:
    return _sel_execution_planner.build(request)


@router.post("/g9-plan", response_model=G9PlanningResponse)
def build_g9_plan(request: G9PlanningRequest) -> G9PlanningResponse:
    return _g9_planner.build(request)


@router.post("/medical-plan", response_model=MedicalPlanningResponse)
def build_medical_plan(request: MedicalPlanningRequest) -> MedicalPlanningResponse:
    return _medical_planner.build(request)


@router.post("/s6/pki-troubleshooting", response_model=PkiTroubleshootingResponse)
def build_s6_pki_troubleshooting(request: PkiTroubleshootingRequest) -> PkiTroubleshootingResponse:
    return _pki_service.build(request)


@router.post("/s2/osint-estimate", response_model=AgentRunResponse)
def build_s2_osint_estimate(request: AgentRunRequest) -> AgentRunResponse:
    context_payload = dict(request.context)
    known_keys = {"user_role", "unit_id", "request_is_training_or_fictional", "extra"}
    unknown_context = {key: value for key, value in context_payload.items() if key not in known_keys}
    if unknown_context:
        extra = dict(context_payload.get("extra") or {})
        extra.update(unknown_context)
        context_payload["extra"] = extra
    context = AgentContext.model_validate(context_payload)
    if context.user_role is None:
        context.user_role = "S-2"
    return _osint_agent.run(request.input, context)


@router.post("/s1/dts-helper", response_model=AdminWorkflowResponse)
def build_s1_dts_helper(request: AdminWorkflowDraftRequest) -> AdminWorkflowResponse:
    return _admin_workflow_builder.build(
        AdminWorkflowRequest(
            workflow_type=AdminWorkflowType.dts_authorization,
            title=request.title,
            facts=request.facts,
            constraints=request.constraints,
        )
    )


@router.post("/s1/gtcc-helper", response_model=AdminWorkflowResponse)
def build_s1_gtcc_helper(request: AdminWorkflowDraftRequest) -> AdminWorkflowResponse:
    return _admin_workflow_builder.build(
        AdminWorkflowRequest(
            workflow_type=AdminWorkflowType.gtcc,
            title=request.title,
            facts=request.facts,
            constraints=request.constraints,
        )
    )


@router.post("/running-estimate", response_model=RunningEstimateResponse)
def build_running_estimate(request: RunningEstimateRequest) -> RunningEstimateResponse:
    return _update_cycle.build_running_estimate(request)


@router.post("/mission-analysis", response_model=MissionAnalysisResponse)
def build_mission_analysis(request: RunningEstimateRequest) -> MissionAnalysisResponse:
    return _update_cycle.build_mission_analysis(request)


@router.post("/cub", response_model=CubResponse)
def build_cub(request: RunningEstimateRequest) -> CubResponse:
    return _update_cycle.build_cub(request)


@router.post("/cpb", response_model=CpbResponse)
def build_cpb(request: RunningEstimateRequest) -> CpbResponse:
    return _update_cycle.build_cpb(request)


@router.post("/update-cycle", response_model=StaffUpdateCycleResponse)
def build_staff_update_cycle(request: RunningEstimateRequest) -> StaffUpdateCycleResponse:
    return _update_cycle.build_update_cycle(request)


@router.post("/planning-cell", response_model=PlanningCellResponse)
def build_planning_cell(request: RunningEstimateRequest) -> PlanningCellResponse:
    return _update_cycle.build_planning_cell(request)


@router.post("/lone-planner", response_model=LonePlannerResponse)
def build_lone_planner(
    request: RunningEstimateRequest,
    section_memory_store: Annotated[SectionMemoryStore, Depends(get_section_memory_store)],
) -> LonePlannerResponse:
    profile = section_memory_store.get(request.user_key) if request.user_key else None
    return _update_cycle.build_lone_planner(request, section_memory=profile)


@router.post("/assisted-section-estimates", response_model=AssistedSectionEstimatesResponse)
def build_assisted_section_estimates(
    request: AssistedSectionEstimateRequest,
    section_memory_store: Annotated[SectionMemoryStore, Depends(get_section_memory_store)],
) -> AssistedSectionEstimatesResponse:
    profile = section_memory_store.get(request.user_key) if request.user_key else None
    return _update_cycle.build_assisted_section_estimates(request, section_memory=profile)
