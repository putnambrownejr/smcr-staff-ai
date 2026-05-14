from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.exercises import ExerciseCadence
from app.schemas.org import OrgChainResponse, OrgUnit
from app.services.org_awareness.exercise_cadence import load_exercise_cadence
from app.services.org_awareness.hierarchy import OrgHierarchyService

router = APIRouter(tags=["org"])

SEED_DIR = Path(__file__).resolve().parents[3] / "data" / "seed"


@lru_cache
def org_service() -> OrgHierarchyService:
    return OrgHierarchyService.from_json(SEED_DIR / "org_units.example.json")


@router.get("/org/units", response_model=list[OrgUnit])
def list_units() -> list[OrgUnit]:
    return org_service().list_units()


@router.get("/org/units/{unit_id}/chain", response_model=OrgChainResponse)
def get_unit_chain(unit_id: str) -> OrgChainResponse:
    chain = org_service().chain_to_root(unit_id)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Unknown unit: {unit_id}")
    return OrgChainResponse(unit_id=unit_id, chain=chain)


@router.get("/exercises", response_model=list[ExerciseCadence])
def list_exercises() -> list[ExerciseCadence]:
    return load_exercise_cadence(SEED_DIR / "exercise_cadence.example.json")
