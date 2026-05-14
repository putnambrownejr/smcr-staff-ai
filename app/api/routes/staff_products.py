from fastapi import APIRouter

from app.schemas.staff_products import StaffProductDraftRequest, StaffProductDraftResponse
from app.services.staff_products.builder import StaffProductBuilder

router = APIRouter(prefix="/staff-products", tags=["staff products"])

_builder = StaffProductBuilder()


@router.post("/draft", response_model=StaffProductDraftResponse)
def draft_staff_product(request: StaffProductDraftRequest) -> StaffProductDraftResponse:
    return _builder.build(request)
