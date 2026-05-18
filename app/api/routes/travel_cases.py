from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.travel_cases import LinkTravelReceiptRequest, TravelCaseListResponse, TravelCaseRecord
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/travel-cases", tags=["travel cases"], dependencies=[LocalApiKeyDependency])


def get_travel_case_store() -> Iterator[TravelCaseStore]:
    yield TravelCaseStore(get_settings().travel_case_storage_dir)


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


@router.get("/{user_key}", response_model=TravelCaseListResponse)
def list_travel_cases(
    user_key: str,
    store: Annotated[TravelCaseStore, Depends(get_travel_case_store)],
) -> TravelCaseListResponse:
    records = store.list_cases(user_key)
    return TravelCaseListResponse(total_cases=len(records), records=records)


@router.get("/{user_key}/{trip_id}", response_model=TravelCaseRecord)
def get_travel_case(
    user_key: str,
    trip_id: str,
    store: Annotated[TravelCaseStore, Depends(get_travel_case_store)],
) -> TravelCaseRecord:
    record = store.get_case(user_key, trip_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown travel case: {trip_id}")
    return record


@router.post("/{user_key}/{trip_id}/link-receipt", response_model=TravelCaseRecord)
def link_travel_receipt(
    user_key: str,
    trip_id: str,
    request: LinkTravelReceiptRequest,
    store: Annotated[TravelCaseStore, Depends(get_travel_case_store)],
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> TravelCaseRecord:
    if request.user_key != user_key:
        raise HTTPException(status_code=400, detail="user_key in path and body must match.")
    context = context_store.get(request.context_id)
    if context is None:
        raise HTTPException(status_code=404, detail=f"Unknown local context item: {request.context_id}")
    if context.document_type not in {"travel_receipt", "dts", "other"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only local context items marked as travel_receipt, dts, or other may be linked to a travel case."
            ),
        )
    try:
        return store.link_receipt(
            user_key=user_key,
            trip_id=trip_id,
            context=context,
            receipt_category=request.receipt_category,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

