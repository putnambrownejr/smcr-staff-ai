from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.battle_rhythm import BattleRhythmBoardResponse, BattleRhythmBoardUpsertRequest
from app.schemas.staff_updates import RunningEstimateRequest
from app.services.staff.battle_rhythm_builder import BattleRhythmBuilder
from app.services.staff.battle_rhythm_store import BattleRhythmStore
from app.services.staff.update_cycle import StaffUpdateCycleBuilder

router = APIRouter(
    prefix="/staff/battle-rhythm",
    tags=["battle rhythm"],
    dependencies=[LocalApiKeyDependency],
)

_builder = BattleRhythmBuilder()
_update_cycle = StaffUpdateCycleBuilder()


def get_battle_rhythm_store() -> Iterator[BattleRhythmStore]:
    settings = get_settings()
    yield BattleRhythmStore(settings.battle_rhythm_storage_dir)


@router.get("/{user_key}", response_model=BattleRhythmBoardResponse)
def get_battle_rhythm_board(
    user_key: str,
    store: Annotated[BattleRhythmStore, Depends(get_battle_rhythm_store)],
) -> BattleRhythmBoardResponse:
    board = store.get(user_key)
    if board is None:
        raise HTTPException(status_code=404, detail=f"No battle rhythm board stored for {user_key}.")
    return board


@router.put("/{user_key}", response_model=BattleRhythmBoardResponse)
def upsert_battle_rhythm_board(
    user_key: str,
    request: BattleRhythmBoardUpsertRequest,
    store: Annotated[BattleRhythmStore, Depends(get_battle_rhythm_store)],
) -> BattleRhythmBoardResponse:
    try:
        return store.upsert(user_key, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{user_key}/from-planning-cell", response_model=BattleRhythmBoardResponse)
def capture_battle_rhythm_from_planning_cell(
    user_key: str,
    request: RunningEstimateRequest,
    store: Annotated[BattleRhythmStore, Depends(get_battle_rhythm_store)],
) -> BattleRhythmBoardResponse:
    planning_cell = _update_cycle.build_planning_cell(request)
    try:
        return store.upsert(user_key, _builder.from_planning_cell(planning_cell))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
