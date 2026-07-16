import asyncio
from pathlib import Path

import httpx
import pytest

from app.schemas.career_opportunities import OpportunitySourceKey
from app.services.ingestion import marforres_opportunity_adapter as adapter_module
from app.services.ingestion.marforres_opportunity_adapter import (
    OFFICIAL_OPPORTUNITY_SOURCES,
    MarforresOpportunityAdapter,
)


def test_adapter_parses_smcr_and_ima_sections() -> None:
    source = OFFICIAL_OPPORTUNITY_SOURCES[OpportunitySourceKey.reserve_billets]
    html = Path("tests/fixtures/marforres_reserve_billets.html").read_text(encoding="utf-8")

    result = MarforresOpportunityAdapter().parse(html, source)

    assert {record.opportunity_type.value for record in result.records} == {"smcr", "ima"}
    assert all(record.source_url == source.url for record in result.records)
    assert result.official_links
    assert result.records[0].published_at is not None


def test_adapter_parses_ados_and_preserves_application_link() -> None:
    source = OFFICIAL_OPPORTUNITY_SOURCES[OpportunitySourceKey.active_billets]
    html = Path("tests/fixtures/marforres_active_billets.html").read_text(encoding="utf-8")

    result = MarforresOpportunityAdapter().parse(html, source)

    assert result.records[0].opportunity_type.value == "ados"
    assert result.records[0].direct_url == "https://forms.osi.apps.mil/r/example-application"
    assert result.records[0].due_date is not None
    # A row with a direct application link and a deadline is highly actionable,
    # so its match score outranks a bare listing (score floor is 0).
    assert result.records[0].match_score is not None
    assert result.records[0].match_score > 0


def test_adapter_rejects_non_allowlisted_source() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        asyncio.run(MarforresOpportunityAdapter().fetch_url("https://example.test/billets"))


def test_adapter_rejects_off_host_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    source = OFFICIAL_OPPORTUNITY_SOURCES[OpportunitySourceKey.reserve_billets]

    class _RedirectingClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "_RedirectingClient":
            return self

        async def __aexit__(self, *exc: object) -> bool:
            return False

        async def get(self, url: str) -> httpx.Response:
            # Simulate an official URL that redirected to an off-host page.
            return httpx.Response(
                200,
                html="<html><body>injected</body></html>",
                headers={"content-type": "text/html"},
                request=httpx.Request("GET", "https://evil.test/billets"),
            )

    monkeypatch.setattr(adapter_module.httpx, "AsyncClient", _RedirectingClient)  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="redirected off"):
        asyncio.run(MarforresOpportunityAdapter().fetch_url(source.url))


def test_layout_without_structured_rows_is_truthful_link_only() -> None:
    source = OFFICIAL_OPPORTUNITY_SOURCES[OpportunitySourceKey.reserve_billets]
    result = MarforresOpportunityAdapter().parse(
        '<a href="https://www.marforres.marines.mil/About/Reserve-Billets/">Open billets</a>',
        source,
    )

    assert result.records == []
    assert result.official_links
    assert "no structured opportunity rows" in result.warnings[0].lower()
