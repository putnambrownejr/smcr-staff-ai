from fastapi.testclient import TestClient

from app.main import app
from app.schemas.pki import PkiIssueType, PkiTroubleshootingRequest
from app.services.admin.pki_support import PkiTroubleshootingService


def test_pki_troubleshooting_service_builds_browser_auth_playbook() -> None:
    service = PkiTroubleshootingService()

    response = service.build(
        PkiTroubleshootingRequest(
            title="MarineNet login issue",
            issue_type=PkiIssueType.browser_auth_issue,
            symptoms=["Certificate prompt never appears in Chrome."],
            browser="Chrome",
            affected_systems=["MarineNet"],
            on_government_furnished_equipment=False,
        )
    )

    assert response.issue_type == PkiIssueType.browser_auth_issue
    assert any("Chrome" in line for line in response.summary_lines)
    assert any("browser" in item.lower() for item in response.likely_causes)
    assert any("certificate prompt" in item.lower() for item in response.immediate_checks)


def test_pki_troubleshooting_route_returns_advisory_response() -> None:
    client = TestClient(app)

    response = client.post(
        "/admin/pki-troubleshooting",
        json={
            "title": "CAC reader issue",
            "issue_type": "cac_not_detected",
            "symptoms": ["The operating system never sees the CAC."],
            "environment_notes": ["Occurs with one reader at home."],
            "affected_systems": ["MarineNet"],
            "on_government_furnished_equipment": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["issue_type"] == "cac_not_detected"
    assert any("advisory only" in warning.lower() for warning in payload["warnings"])
    assert payload["immediate_checks"]
