from fastapi import APIRouter

from app.core.auth import LocalApiKeyDependency
from app.schemas.planning import (
    FragoToConopRequest,
    FragoToConopResponse,
    StaffPlanningPackageRequest,
    StaffPlanningPackageResponse,
)
from app.services.planning.frago_conop_builder import FragoToConopBuilder
from app.services.planning.orchestrator import StaffPlanningOrchestrator

router = APIRouter(prefix="/planning", tags=["planning workflows"], dependencies=[LocalApiKeyDependency])
_orchestrator = StaffPlanningOrchestrator()
_frago_conop = FragoToConopBuilder()


@router.post("/staff-package", response_model=StaffPlanningPackageResponse)
def build_staff_package(request: StaffPlanningPackageRequest) -> StaffPlanningPackageResponse:
    return _orchestrator.build(request)


@router.post("/frago-to-conop", response_model=FragoToConopResponse)
def build_frago_to_conop(request: FragoToConopRequest) -> FragoToConopResponse:
    return _frago_conop.build(request)
