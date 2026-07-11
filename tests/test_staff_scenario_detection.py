import pytest

from app.services.agents.staff_advisor_agent import _detect_scenario


@pytest.mark.parametrize(
    "text",
    [
        "Help structure the support request for our next exercise.",
        "Review the broadcast plan for this exercise.",
        "Assess workmanship during the exercise.",
        "Plan an exercise near Indianapolis.",
    ],
)
def test_scenario_detection_rejects_substring_false_positives(text: str) -> None:
    assert _detect_scenario(text) is False


@pytest.mark.parametrize(
    "text",
    [
        "Exercise in India after the port was damaged.",
        "Earthquake exercise with 500 displaced people and a damaged road.",
        "Training scenario in Japan with effects extending 20 km.",
    ],
)
def test_scenario_detection_accepts_complete_signals(text: str) -> None:
    assert _detect_scenario(text) is True
