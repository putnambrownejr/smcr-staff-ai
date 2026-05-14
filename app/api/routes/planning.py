from fastapi import APIRouter

from app.schemas.planning import StaffPlanningPackageRequest, StaffPlanningPackageResponse
from app.services.planning.orchestrator import StaffPlanningOrchestrator

router = APIRouter(prefix="/planning", tags=["planning workflows"])
_orchestrator = StaffPlanningOrchestrator()


@router.post("/staff-package", response_model=StaffPlanningPackageResponse)
def build_staff_package(request: StaffPlanningPackageRequest) -> StaffPlanningPackageResponse:
    return _orchestrator.build(request)
