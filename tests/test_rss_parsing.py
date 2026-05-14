from pathlib import Path
from typing import cast

from app.services.ingestion.maradmin_scraper import normalize_message_records, normalize_messages
from app.services.ingestion.rss_client import parse_feed


def test_rss_parsing_from_fixture() -> None:
    xml_text = Path("tests/fixtures/sample_maradmin_feed.xml").read_text(encoding="utf-8")
    items = parse_feed(xml_text)

    assert len(items) == 2
    assert items[0].title == "Reserve Officer PME Training Update"
    assert items[0].published_at is not None


def test_maradmin_relevance_tags() -> None:
    xml_text = Path("tests/fixtures/sample_maradmin_feed.xml").read_text(encoding="utf-8")
    messages = normalize_messages(parse_feed(xml_text))
    first_tags = cast(list[str], messages[0]["tags"])
    second_tags = cast(list[str], messages[1]["tags"])

    assert {"Reserve", "Officer", "PME", "Training"}.issubset(set(first_tags))
    assert "Uniform" in second_tags


def test_maradmin_records_are_idempotent_and_cited() -> None:
    xml_text = Path("tests/fixtures/sample_maradmin_feed.xml").read_text(encoding="utf-8")
    records = normalize_message_records(parse_feed(xml_text))

    assert records[0].source_id.startswith("maradmin-")
    assert records[0].canonical_url
    assert records[0].source_hash
