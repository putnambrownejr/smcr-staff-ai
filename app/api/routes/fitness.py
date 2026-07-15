from fastapi import APIRouter

from app.core.auth import LocalApiKeyDependency
from app.schemas.fitness import UnitPtPlan, UnitPtPlanRequest
from app.services.fitness.unit_pt_planner import build_unit_pt_plan

router = APIRouter(prefix="/fitness", tags=["fitness"], dependencies=[LocalApiKeyDependency])


@router.post("/unit-pt/plan", response_model=UnitPtPlan)
def plan_unit_pt(request: UnitPtPlanRequest) -> UnitPtPlan:
    return build_unit_pt_plan(request)
