import pytest
from pydantic import ValidationError

from app.schemas.fitness import UnitPtPlanRequest
from app.services.fitness.unit_pt_planner import build_unit_pt_plan


@pytest.mark.parametrize("count", [4, 51])
def test_unit_pt_request_rejects_out_of_range_counts(count: int) -> None:
    with pytest.raises(ValidationError):
        UnitPtPlanRequest(participant_count=count)


@pytest.mark.parametrize(
    ("count", "band"),
    [(5, "small element"), (12, "small element"), (13, "two-lane"), (24, "two-lane"), (25, "station"), (50, "station")],
)
def test_unit_pt_planner_scales_organization(count: int, band: str) -> None:
    plan = build_unit_pt_plan(UnitPtPlanRequest(participant_count=count))
    assert band in plan.scaling_band
    assert sum(block.minutes for block in plan.blocks) == 60
    assert {review.role for review in plan.staff_reviews} >= {"S-3 / OpsO", "S-4", "SgtMaj / SEL", "ORM"}
    assert len(plan.orm.hazards) >= 5
    assert plan.footer.startswith("DRAFT")


def test_unit_pt_planner_respects_cadence_and_partial_constraints() -> None:
    plan = build_unit_pt_plan(
        UnitPtPlanRequest(
            participant_count=20,
            duration_minutes=45,
            cadence_preference="Reserve Ready",
            limitations=["one low-impact lane"],
        )
    )
    assert plan.cadence == "Reserve Ready"
    assert sum(block.minutes for block in plan.blocks) == 45
    assert any("medical" in warning.lower() for warning in plan.warnings)
