from pathlib import Path

from app.services.reading.live_catalog import ReadingListRemoteCatalogService

_SAMPLE_ALMAR_HTML = """
<html>
  <body>
    <h1>UPDATE TO THE COMMANDANT'S PROFESSIONAL READING LIST FOR FISCAL YEAR 26</h1>
    <div>
      <p>3.a. Commandant's Choice: "Once an Eagle" by A. Myrer</p>
      <p>3.b. Heritage</p>
      <p>3.b.1. "With the Old Breed: At Peleliu and Okinawa" by Eugene B. Sledge</p>
      <p>3.e. Strategy</p>
      <p>3.e.1. "Fleet Tactics and Naval Operations" by Wayne P. Hughes and Robert P. Girrier</p>
      <p>3.f. Foundational</p>
      <p>3.f.1. "MCDP 1 Warfighting" by United States Marine Corps</p>
    </div>
  </body>
</html>
"""


def test_live_reading_catalog_parser_merges_seed_metadata_and_categories() -> None:
    service = ReadingListRemoteCatalogService(Path("data/seed/reading_list.example.yaml"))

    catalog = service.parse_official_current_catalog(_SAMPLE_ALMAR_HTML)

    titles = {book.title: book for book in catalog.books}
    assert "Once an Eagle" in titles
    assert "Fleet Tactics and Naval Operations" in titles
    assert "MCDP 1 Warfighting" in titles
    assert "commandants_choice" in titles["Once an Eagle"].categories
    assert "current_list" in titles["Fleet Tactics and Naval Operations"].categories
    assert titles["Fleet Tactics and Naval Operations"].summary
    assert any("marines.mil" in url for url in titles["MCDP 1 Warfighting"].source_urls)
