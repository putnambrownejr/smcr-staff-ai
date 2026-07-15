from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.cadences import CadenceCreateRequest, CadenceLibraryResponse, CadenceRecord
from app.services.fitness.cadence_store import CadenceStore

router = APIRouter(prefix="/cadences", tags=["cadences"], dependencies=[LocalApiKeyDependency])


def get_cadence_store() -> Iterator[CadenceStore]:
    yield CadenceStore(get_settings().cadence_storage_dir)


@router.get("/{user_key}", response_model=CadenceLibraryResponse)
def list_cadences(
    user_key: str,
    store: Annotated[CadenceStore, Depends(get_cadence_store)],
    include_adult: bool = False,
) -> CadenceLibraryResponse:
    return CadenceLibraryResponse(
        records=store.list_records(user_key, include_adult=include_adult),
        adult_content_included=include_adult,
    )


@router.post("/{user_key}", response_model=CadenceRecord, status_code=201)
def create_cadence(
    user_key: str,
    request: CadenceCreateRequest,
    store: Annotated[CadenceStore, Depends(get_cadence_store)],
) -> CadenceRecord:
    if user_key != request.user_key:
        raise HTTPException(status_code=400, detail="user_key in path and body must match.")
    try:
        return store.create(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{user_key}/{cadence_id}", status_code=204)
def delete_cadence(
    user_key: str,
    cadence_id: str,
    store: Annotated[CadenceStore, Depends(get_cadence_store)],
) -> None:
    if not store.delete(user_key, cadence_id):
        raise HTTPException(status_code=404, detail=f"Unknown or built-in cadence: {cadence_id}")
