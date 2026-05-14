from fastapi import APIRouter

from app.schemas.poam import PoamRequest, PoamResponse
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductDraftResponse
from app.services.staff_products.builder import StaffProductBuilder
from app.services.staff_products.poam_builder import PoamBuilder

router = APIRouter(prefix="/staff-products", tags=["staff products"])

_builder = StaffProductBuilder()
_poam_builder = PoamBuilder()


@router.post("/draft", response_model=StaffProductDraftResponse)
def draft_staff_product(request: StaffProductDraftRequest) -> StaffProductDraftResponse:
    return _builder.build(request)


@router.post("/poam", response_model=PoamResponse)
def build_poam(request: PoamRequest) -> PoamResponse:
    return _poam_builder.build(request)
