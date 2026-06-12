from collections.abc import Callable

from fastapi import APIRouter, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.schemas.tdg import TdgGenerationRequest, TdgGenerationResponse
from app.schemas.training import (
    AnnualTrainingPlanRequest,
    AnnualTrainingPlanResponse,
    InfantryTrainingPackageRequest,
    InfantryTrainingPackageResponse,
    RangePackageRequest,
    RangePackageResponse,
    RangeSafetyRequest,
    RangeSafetyResponse,
    S3PlanningRequest,
    S3PlanningResponse,
    S4PlanningRequest,
    S4PlanningResponse,
    ScenarioPresetListResponse,
    TrainingCaseStudyRequest,
    TrainingCaseStudyResponse,
    TrainingScenarioRequest,
    TrainingScenarioResponse,
)
from app.services.training.case_study_builder import TrainingCaseStudyBuilder
from app.services.training.event_planner import AnnualTrainingPlanner, RangePackagePlanner
from app.services.training.infantry_package_builder import InfantryTrainingPackageBuilder
from app.services.training.s3_planner import S3Planner
from app.services.training.s4_planner import S4Planner
from app.services.training.scenario_builder import RangeSafetyBuilder, TrainingScenarioBuilder
from app.services.training.scenario_preset_catalog import ScenarioPresetCatalog
from app.services.training.tdg_builder import TdgBuilder

router = APIRouter(prefix="/training", tags=["training workflows"], dependencies=[LocalApiKeyDependency])


def _apply_preset[T](fn: Callable[[], T], preset_id: str | None) -> T:
    try:
        return fn()
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario preset: {preset_id}",
        ) from exc


_scenario_builder = TrainingScenarioBuilder()
_scenario_presets = ScenarioPresetCatalog.default()
_range_builder = RangeSafetyBuilder()
_annual_training_planner = AnnualTrainingPlanner()
_range_package_planner = RangePackagePlanner()
_tdg_builder = TdgBuilder()
_s3_planner = S3Planner()
_s4_planner = S4Planner()
_case_study_builder = TrainingCaseStudyBuilder()
_infantry_package_builder = InfantryTrainingPackageBuilder()


@router.get("/scenario-presets", response_model=ScenarioPresetListResponse)
def list_scenario_presets() -> ScenarioPresetListResponse:
    return _scenario_presets.list()


@router.post("/scenario", response_model=TrainingScenarioResponse)
def build_training_scenario(request: TrainingScenarioRequest) -> TrainingScenarioResponse:
    if request.scenario_preset_id:
        request = _apply_preset(
            lambda: _scenario_presets.apply_to_training_request(request),
            request.scenario_preset_id,
        )
    return _scenario_builder.build(request)


@router.post("/range-safety", response_model=RangeSafetyResponse)
def build_range_safety_plan(request: RangeSafetyRequest) -> RangeSafetyResponse:
    return _range_builder.build(request)


@router.post("/annual-training-plan", response_model=AnnualTrainingPlanResponse)
def build_annual_training_plan(request: AnnualTrainingPlanRequest) -> AnnualTrainingPlanResponse:
    return _annual_training_planner.build(request)


@router.post("/range-package", response_model=RangePackageResponse)
def build_range_package(request: RangePackageRequest) -> RangePackageResponse:
    return _range_package_planner.build(request)


@router.post("/tdg", response_model=TdgGenerationResponse)
def build_tdg(request: TdgGenerationRequest) -> TdgGenerationResponse:
    return _tdg_builder.build(request)


@router.post("/case-study", response_model=TrainingCaseStudyResponse)
def build_training_case_study(request: TrainingCaseStudyRequest) -> TrainingCaseStudyResponse:
    return _case_study_builder.build(request)


@router.post("/s3-plan", response_model=S3PlanningResponse)
def build_s3_plan(request: S3PlanningRequest) -> S3PlanningResponse:
    if request.scenario_preset_id:
        request = _apply_preset(lambda: _scenario_presets.apply_to_s3_request(request), request.scenario_preset_id)
    return _s3_planner.build(request)


@router.post("/s4-plan", response_model=S4PlanningResponse)
def build_s4_plan(request: S4PlanningRequest) -> S4PlanningResponse:
    return _s4_planner.build(request)


@router.post("/infantry-package", response_model=InfantryTrainingPackageResponse)
def build_infantry_training_package(request: InfantryTrainingPackageRequest) -> InfantryTrainingPackageResponse:
    return _infantry_package_builder.build(request)
