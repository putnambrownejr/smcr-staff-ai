from fastapi import APIRouter

from app.schemas.tdg import TdgGenerationRequest, TdgGenerationResponse
from app.schemas.training import (
    AnnualTrainingPlanRequest,
    AnnualTrainingPlanResponse,
    RangePackageRequest,
    RangePackageResponse,
    RangeSafetyRequest,
    RangeSafetyResponse,
    S3PlanningRequest,
    S3PlanningResponse,
    S4PlanningRequest,
    S4PlanningResponse,
    TrainingCaseStudyRequest,
    TrainingCaseStudyResponse,
    TrainingScenarioRequest,
    TrainingScenarioResponse,
)
from app.services.training.case_study_builder import TrainingCaseStudyBuilder
from app.services.training.event_planner import AnnualTrainingPlanner, RangePackagePlanner
from app.services.training.s3_planner import S3Planner
from app.services.training.s4_planner import S4Planner
from app.services.training.scenario_builder import RangeSafetyBuilder, TrainingScenarioBuilder
from app.services.training.tdg_builder import TdgBuilder

router = APIRouter(prefix="/training", tags=["training workflows"])
_scenario_builder = TrainingScenarioBuilder()
_range_builder = RangeSafetyBuilder()
_annual_training_planner = AnnualTrainingPlanner()
_range_package_planner = RangePackagePlanner()
_tdg_builder = TdgBuilder()
_s3_planner = S3Planner()
_s4_planner = S4Planner()
_case_study_builder = TrainingCaseStudyBuilder()


@router.post("/scenario", response_model=TrainingScenarioResponse)
def build_training_scenario(request: TrainingScenarioRequest) -> TrainingScenarioResponse:
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
    return _s3_planner.build(request)


@router.post("/s4-plan", response_model=S4PlanningResponse)
def build_s4_plan(request: S4PlanningRequest) -> S4PlanningResponse:
    return _s4_planner.build(request)
