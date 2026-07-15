import pytest
from pydantic import ValidationError

from app.schemas.staff import G9OperatingContext, G9PlanningRequest
from app.services.staff.g9_planner import G9Planner


def test_g9_request_accepts_typed_civil_context_inputs() -> None:
    request = G9PlanningRequest(
        title="County support exercise",
        supported_problem="Plan civil-military coordination for a hurricane exercise.",
        operating_context=G9OperatingContext.domestic_support,
        source_items=[
            {
                "title": "County emergency plan",
                "claim": "The county publishes a shelter coordination process.",
                "source_type": "local-government",
                "corroborated": True,
                "retrieved_at": "2026-07-15",
            }
        ],
        infrastructure_systems=[
            {"system": "water", "condition_or_concern": "Continuity during storm response"}
        ],
        cultural_context_items=[
            {
                "documented_context": "Use accessible public-information formats.",
                "planning_relevance": "Coordinate accessible public information.",
            }
        ],
    )

    assert request.operating_context is G9OperatingContext.domestic_support
    assert request.infrastructure_systems[0].system == "water"
    assert request.source_items[0].retrieved_at == "2026-07-15"


def test_g9_request_rejects_blank_required_civil_context_fields() -> None:
    with pytest.raises(ValidationError):
        G9PlanningRequest(
            title="Exercise",
            supported_problem="Support a civil-military exercise.",
            infrastructure_systems=[{"system": ""}],
        )


def test_g9_request_rejects_invalid_source_retrieval_date() -> None:
    with pytest.raises(ValidationError):
        G9PlanningRequest(
            title="Exercise",
            supported_problem="Support a civil-military exercise.",
            source_items=[{"title": "Source", "retrieved_at": "not-a-date"}],
        )


def test_g9_planner_builds_domestic_civil_context_sections() -> None:
    response = G9Planner().build(
        G9PlanningRequest(
            title="County support exercise",
            supported_problem="Coordinate civil support in a hurricane exercise.",
            operating_context=G9OperatingContext.domestic_support,
            source_items=[
                {
                    "title": "County plan",
                    "claim": "The county publishes a shelter coordination process.",
                    "source_type": "local-government",
                    "corroborated": True,
                }
            ],
            infrastructure_systems=[
                {"system": "water", "known_dependency": "power continuity"}
            ],
            cultural_context_items=[
                {
                    "documented_context": "Use accessible public-information formats.",
                    "regional_variation": "Confirm language needs with local partners.",
                }
            ],
        )
    )

    assert any("civilian lead" in item.lower() for item in response.operating_context_frame)
    assert any("water" in item.lower() for item in response.infrastructure_dependency_assessment)
    assert any("variation" in item.lower() for item in response.cultural_context_assessment)
    assert response.evidence_and_assumptions[0].kind == "reported_fact"
    assert len(response.civil_estimate_outline) == 8


def test_g9_planner_marks_unsourced_claim_as_assumption() -> None:
    response = G9Planner().build(
        G9PlanningRequest(
            title="Partner exercise",
            supported_problem="Prepare civil-military context.",
            operating_context=G9OperatingContext.overseas_partner,
            source_items=[{"title": "Unattributed note", "claim": "A local service may be constrained."}],
        )
    )

    assert response.evidence_and_assumptions[0].kind == "planning_assumption"
    assert response.evidence_and_assumptions[0].confidence == "low"


def test_g9_planner_keeps_legacy_request_valid_and_flags_context_gap() -> None:
    response = G9Planner().build(
        G9PlanningRequest(title="Legacy request", supported_problem="Prepare a civil-military event.")
    )

    assert response.operating_context_frame
    assert any("operating context" in item.lower() for item in response.information_requirements)


def test_g9_planner_includes_exact_draft_footer() -> None:
    response = G9Planner().build(
        G9PlanningRequest(title="Exercise", supported_problem="Prepare a civil-military event.")
    )

    assert "DRAFT — Verify all references against current official sources before acting." in response.warnings


def test_g9_planner_withholds_sensitive_text_from_response() -> None:
    sensitive_text = "Current movement for convoy route is withheld"
    response = G9Planner().build(
        G9PlanningRequest(
            title="Exercise",
            supported_problem="Prepare a civil-military event.",
            civil_considerations=[sensitive_text],
        )
    )

    assert any("detected" in warning.lower() for warning in response.warnings)
    assert sensitive_text not in response.model_dump_json()
