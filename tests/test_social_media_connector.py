from app.schemas.social import SocialIngestRequest, SocialSourceType, SocialTrendInput
from app.services.ingestion.social_media_connector import SocialMediaVettedConnector


def test_social_connector_normalizes_osint_source_items() -> None:
    connector = SocialMediaVettedConnector()
    request = SocialIngestRequest(
        topic="Reserve recruiting public discussion",
        records=[
            SocialTrendInput(
                title="Official post",
                url="https://example.test/official-post",
                publisher="Example official source",
                source_type=SocialSourceType.official,
                summary="Official public update about a recruiting event.",
                claim="A public recruiting event was announced.",
                corroborated=True,
            ),
            SocialTrendInput(
                title="Public trend summary",
                url="https://example.test/social-trend",
                publisher="Example platform export",
                source_type=SocialSourceType.social_trend,
                platform="example-social",
                summary="Topic-level public discussion increased around the event.",
                trend_signal="Increased public mentions of the recruiting event.",
                counterargument="Platform discussion may reflect amplification.",
            ),
        ],
    )

    response = connector.ingest(request)

    assert response.records_seen == 2
    assert response.records_accepted == 2
    assert response.osint_source_items[0]["source_type"] == "official"
    assert response.osint_source_items[1]["trend_signal"] == "Increased public mentions of the recruiting event."


def test_social_connector_strict_mode_blocks_person_targeting() -> None:
    connector = SocialMediaVettedConnector()
    request = SocialIngestRequest(
        records=[
            SocialTrendInput(
                title="Bad record",
                url="https://example.test/post",
                publisher="Example social",
                source_type=SocialSourceType.social_trend,
                summary="Find a private profile and home address.",
                trend_signal="Mentions of a private profile.",
            )
        ],
        strict_vetting=True,
    )

    response = connector.ingest(request)

    assert response.records_seen == 1
    assert response.records_accepted == 0
    assert any("person-targeted" in warning for warning in response.warnings)
