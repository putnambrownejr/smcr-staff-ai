from fastapi import APIRouter, HTTPException

from app.schemas.staff import (
    StaffCouncilRequest,
    StaffCouncilResponse,
    StaffRoleMetadata,
    StaffRoundRobinRequest,
    StaffRoundRobinResponse,
)
from app.services.staff.council import StaffCouncilService

router = APIRouter(prefix="/staff", tags=["staff council"])

_service = StaffCouncilService()


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
