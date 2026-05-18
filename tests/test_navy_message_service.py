from app.services.ingestion.navy_message_service import NavyMessageService

_SAMPLE_NAVADMIN_HTML = """
<html>
  <body>
    <p>106/26 FISCAL YEAR 2027 RESERVE OFFICER RETENTION AND CONTINUATION BOARDS 05/06/2026</p>
    <p>101/26 NAVY UNIFORM UPDATES TO NAVY WORKING UNIFORM AND SERVICE DRESS BLUES 04/29/2026</p>
  </body>
</html>
"""


def test_navy_message_parser_extracts_current_year_table_rows() -> None:
    service = NavyMessageService()

    records = service.parse_year_page(
        _SAMPLE_NAVADMIN_HTML,
        source_family="NAVADMIN",
        source_url="https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN-2026/",
    )

    assert len(records) == 2
    assert records[0].message_number == "106/26"
    assert records[0].source_family == "NAVADMIN"
    assert "Reserve" in records[0].tags
    assert records[1].title.startswith("NAVY UNIFORM UPDATES")
