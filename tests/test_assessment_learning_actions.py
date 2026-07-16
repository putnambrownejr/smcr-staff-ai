from app.schemas.agents import ScenarioOutputStatus
from app.services.agents.assessment_learning_agent import build_assessment_learning_agent
from app.services.agents.base import AgentContext


def test_assessment_agent_outputs_owned_measurable_correction() -> None:
    response = build_assessment_learning_agent().run(
        "AAR: radio checks were late and no owner was assigned.",
        AgentContext(),
    )

    assert "Corrective-action register" in response.answer
    assert "Next-drill verification condition" in response.answer
    assert "Status: Open" in response.answer
    assert response.answer.endswith("DRAFT — Verify all references against current official sources before acting.")
    assert response.scenario_output_status == ScenarioOutputStatus.validated
    assert response.scenario_output is not None
    record = response.scenario_output["corrective_action_register"][0]
    assert record["owner"] == "Not provided — human assignment required"
    assert record["standard_or_measure"] == "Not provided"
    assert record["suspense"] == "Not provided — human assignment required"
    assert record["next_drill_verification_condition"] == "Not provided"


def test_assessment_agent_flags_missing_measure_or_owner() -> None:
    response = build_assessment_learning_agent().run("Attendance was good.", AgentContext())

    assert "Missing evidence or ownership" in response.answer
    assert "Standard or measure not provided" in response.answer
    assert "Owner not provided" in response.answer
    assert "completion cannot be inferred" in response.answer


def test_assessment_agent_preserves_explicit_aar_fields_without_inference() -> None:
    response = build_assessment_learning_agent().run(
        """Observation: Radio checks started 20 minutes late.
Standard: Complete radio checks before the rehearsal start time.
Root cause: The communications roster was not published.
Corrective action: Publish the roster at the pre-drill planning meeting.
Owner: S-6 representative.
Suspense: Before the next drill.
Verification condition: The evaluator records the check completion time at the next rehearsal.""",
        AgentContext(),
    )

    assert response.scenario_output is not None
    record = response.scenario_output["corrective_action_register"][0]
    assert record["owner"] == "S-6 representative."
    assert record["suspense"] == "Before the next drill."
    assert record["next_drill_verification_condition"].startswith("The evaluator")
    assert "Status: Open — completion has not been evidenced or inferred." in response.answer
