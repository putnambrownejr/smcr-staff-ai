from fastapi import APIRouter, HTTPException

from app.schemas.staff import (
    S2EstimateRequest,
    S2EstimateResponse,
    S6PlanRequest,
    S6PlanResponse,
    StaffCouncilRequest,
    StaffCouncilResponse,
    StaffRoleMetadata,
    StaffRoundRobinRequest,
    StaffRoundRobinResponse,
)
from app.services.staff.council import StaffCouncilService
from app.services.staff.s2_estimator import S2Estimator
from app.services.staff.s6_planner import S6Planner

router = APIRouter(prefix="/staff", tags=["staff council"])

_service = StaffCouncilService()
_s2_estimator = S2Estimator()
_s6_planner = S6Planner()


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


@router.post("/s6-plan", response_model=S6PlanResponse)
def build_s6_plan(request: S6PlanRequest) -> S6PlanResponse:
    return _s6_planner.build(request)
