from pathlib import Path

from pydantic import ValidationError

from app.schemas.billets import BilletSearchRequest, BilletUserProfile
from app.services.billets.recommender import recommend_billets
from app.services.ingestion.smcr_bic_scraper import SmcrBicScraper


def test_smcr_bic_scraper_parses_fixture() -> None:
    html = Path("tests/fixtures/sample_billets.html").read_text(encoding="utf-8")
    billets, links = SmcrBicScraper().parse(html, "https://www.marforres.marines.mil/Billets/")

    assert "https://reservehub.swf.army.mil/" in links
    assert len(billets) == 2
    assert billets[0].bic == "M1234567890"
    assert billets[0].mos == "0602"


def test_billet_recommendations_rank_relevant_matches() -> None:
    html = Path("tests/fixtures/sample_billets.html").read_text(encoding="utf-8")
    billets, _ = SmcrBicScraper().parse(html, "https://www.marforres.marines.mil/Billets/")
    profile = BilletUserProfile(
        mos="0602",
        rank="Capt",
        desired_locations=["Austin"],
        keywords=["communications"],
    )

    recommendations = recommend_billets(billets, profile)

    assert recommendations
    assert recommendations[0].billet.title == "Communications Officer"
    assert recommendations[0].score > recommendations[-1].score
    assert any("MOS match" in reason for reason in recommendations[0].match_reasons)


def test_billet_search_request_rejects_arbitrary_source_url() -> None:
    try:
        BilletSearchRequest.model_validate(
            {
                "profile": {"mos": "0602"},
                "source_url": "https://example.test/billets",
            }
        )
    except ValidationError:
        assert True
    else:
        raise AssertionError("Expected arbitrary source_url to be rejected")
