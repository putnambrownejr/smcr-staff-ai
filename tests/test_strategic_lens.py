import pytest

from app.schemas.strategic_lens import StrategicLensRequest
from app.services.training.strategic_lens import StrategicLensBuilder


def test_fictional_lens_requires_two_to_four_distinct_cards() -> None:
    builder = StrategicLensBuilder()
    with pytest.raises(ValueError, match="two to four"):
        builder.build(
            StrategicLensRequest(
                mode="fictional",
                actor_name="Aster Guard",
                fictional_actor_confirmed=True,
                posture_cards=["indirect_leverage"],
            ),
            [],
        )
    with pytest.raises(ValueError, match="two to four"):
        builder.build(
            StrategicLensRequest(
                mode="fictional",
                actor_name="Aster Guard",
                fictional_actor_confirmed=True,
                posture_cards=["indirect_leverage", "indirect_leverage"],
            ),
            [],
        )


def test_fictional_lens_marks_outputs_as_scenario_assumptions() -> None:
    lens = StrategicLensBuilder().build(
        StrategicLensRequest(
            mode="fictional",
            actor_name="Aster Guard",
            fictional_actor_confirmed=True,
            posture_cards=["indirect_leverage", "information_contest"],
        ),
        [],
    )
    assert all(item.startswith("Scenario assumption:") for item in lens.strategic_objective)
    assert "real-world forecast" in lens.hypotheses[0]


def test_fictional_lens_requires_confirmation_that_actor_is_fictional() -> None:
    with pytest.raises(ValueError, match="confirmation"):
        StrategicLensBuilder().build(
            StrategicLensRequest(
                mode="fictional", actor_name="Aster Guard", posture_cards=["indirect_leverage", "information_contest"]
            ),
            [],
        )


def test_public_source_lens_requires_reviewed_local_evidence() -> None:
    builder = StrategicLensBuilder()
    request = StrategicLensRequest(mode="public_source", actor_name="Example force")
    with pytest.raises(ValueError, match="reviewed local evidence"):
        builder.build(request, [])
    with pytest.raises(ValueError, match="reviewed local evidence"):
        builder.build(request, [{"title": "Source", "excerpt": "Text", "source_hash": "hash", "trust_status": "watch"}])


def test_public_lens_preserves_local_source_provenance() -> None:
    source_item = {
        "title": "Public review",
        "excerpt": "A public-source excerpt for a training assessment.",
        "source_hash": "bridge-hash",
        "retrieved_at": "2026-07-15T00:00:00+00:00",
        "url": "https://example.test/public-review",
        "publisher": "Example publisher",
        "trust_status": "current",
    }
    lens = StrategicLensBuilder().build(
        StrategicLensRequest(mode="public_source", actor_name="Example force"), [source_item]
    )
    assert "bridge-hash" in lens.source_hashes
    assert lens.evidence_observations
    assert lens.competing_interpretation
    assert lens.discriminator
    assert not lens.strategic_objective
    assert lens.evidence_provenance[0].url == source_item["url"]
    assert lens.evidence_provenance[0].publisher == source_item["publisher"]
    assert lens.evidence_provenance[0].retrieved_at == source_item["retrieved_at"]
    assert lens.evidence_provenance[0].trust_status == "current"
