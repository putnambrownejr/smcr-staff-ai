from fastapi import APIRouter

from app.schemas.training import (
    RangeSafetyRequest,
    RangeSafetyResponse,
    TrainingScenarioRequest,
    TrainingScenarioResponse,
)
from app.services.training.scenario_builder import RangeSafetyBuilder, TrainingScenarioBuilder

router = APIRouter(prefix="/training", tags=["training workflows"])
_scenario_builder = TrainingScenarioBuilder()
_range_builder = RangeSafetyBuilder()


@router.post("/scenario", response_model=TrainingScenarioResponse)
def build_training_scenario(request: TrainingScenarioRequest) -> TrainingScenarioResponse:
    return _scenario_builder.build(request)


@router.post("/range-safety", response_model=RangeSafetyResponse)
def build_range_safety_plan(request: RangeSafetyRequest) -> RangeSafetyResponse:
    return _range_builder.build(request)
