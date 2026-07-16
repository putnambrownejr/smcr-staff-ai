import asyncio
from pathlib import Path

import httpx
import pytest
from bs4 import BeautifulSoup
from pydantic import ValidationError

from app.schemas.billets import BilletSearchRequest, BilletUserProfile
from app.services.billets.recommender import recommend_billets
from app.services.ingestion import smcr_bic_scraper as scraper_module
from app.services.ingestion.smcr_bic_scraper import (
    MARFORRES_BILLETS_URL,
    SmcrBicScraper,
    parse_billet_cards,
)


def test_scraper_rejects_non_allowlisted_url() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        asyncio.run(SmcrBicScraper().fetch_html("https://example.test/billets"))


def test_scraper_rejects_off_host_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    class _RedirectingClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "_RedirectingClient":
            return self

        async def __aexit__(self, *exc: object) -> bool:
            return False

        async def get(self, url: str) -> httpx.Response:
            return httpx.Response(
                200,
                html="<html><body>injected</body></html>",
                request=httpx.Request("GET", "https://evil.test/billets"),
            )

    monkeypatch.setattr(scraper_module.httpx, "AsyncClient", _RedirectingClient)  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="redirected off"):
        asyncio.run(SmcrBicScraper().fetch_html(MARFORRES_BILLETS_URL))


def test_smcr_bic_scraper_parses_fixture() -> None:
    html = Path("tests/fixtures/sample_billets.html").read_text(encoding="utf-8")
    billets, links = SmcrBicScraper().parse(html, "https://www.marforres.marines.mil/Billets/")

    assert "https://reservehub.swf.army.mil/" in links
    assert len(billets) == 2
    assert billets[0].bic == "M1234567890"
    assert billets[0].mos == "0602"


def test_billet_card_parser_selects_data_bic_attributes() -> None:
    soup = BeautifulSoup(
        '<div data-bic="M1234567892" data-title="Operations Officer" data-unit="Example Unit"></div>',
        "html.parser",
    )

    billets = parse_billet_cards(soup, "https://www.marforres.marines.mil/Billets/")

    assert len(billets) == 1
    assert billets[0].bic == "M1234567892"
    assert billets[0].title == "Operations Officer"


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
