from fastapi.testclient import TestClient

from app.main import app


def test_correspondence_conversion_returns_navmac_style_sections() -> None:
    client = TestClient(app)

    response = client.post(
        "/personnel/convert-correspondence",
        json={
            "format_type": "naval_letter",
            "title": "Travel support request",
            "purpose": "Request travel support for upcoming reserve drill attendance.",
            "audience": "Battalion S-1",
            "source_text": "Need a formal request for travel support tied to next month's drill.",
            "references": ["Orders"],
            "enclosures": ["Orders", "Travel estimate"],
            "constraints": ["Keep the tone formal and concise"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["required_headers"]
    assert payload["sections"]
    assert any("5216" in citation["title"] for citation in payload["structured_citations"])
    assert any("human review" in warning.lower() for warning in payload["warnings"])
