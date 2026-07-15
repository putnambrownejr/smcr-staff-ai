import asyncio
from pathlib import Path

import pytest

from app.schemas.career_opportunities import OpportunitySourceKey
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


def test_adapter_rejects_non_allowlisted_source() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        asyncio.run(MarforresOpportunityAdapter().fetch_url("https://example.test/billets"))


def test_layout_without_structured_rows_is_truthful_link_only() -> None:
    source = OFFICIAL_OPPORTUNITY_SOURCES[OpportunitySourceKey.reserve_billets]
    result = MarforresOpportunityAdapter().parse(
        '<a href="https://www.marforres.marines.mil/About/Reserve-Billets/">Open billets</a>',
        source,
    )

    assert result.records == []
    assert result.official_links
    assert "no structured opportunity rows" in result.warnings[0].lower()
