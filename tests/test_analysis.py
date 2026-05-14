from fastapi.testclient import TestClient

from app.main import app


def test_analysis_summary_route_extracts_actions_and_due_outs() -> None:
    client = TestClient(app)

    response = client.post(
        "/analysis/summarize",
        json={
            "focus": "drill weekend prep",
            "text": (
                "Planning notes for the next drill weekend.\n"
                "- Confirm muster timeline with company office.\n"
                "- DTS voucher due NLT 06/10/2026.\n"
                "- Prepare uniform and pack field gear.\n"
                "Need to review the training lane sequence before Friday."
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stored"] is False
    assert "DTS voucher due NLT 06/10/2026." in payload["due_outs"]
    assert any("Confirm muster timeline" in item for item in payload["action_items"])
    assert payload["summary_points"]


def test_analysis_summary_route_limits_sensitive_content() -> None:
    client = TestClient(app)

    response = client.post(
        "/analysis/summarize",
        json={"text": "Current movement plan with call sign RAVEN and frequency 305.5 must be updated."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary_points"][0].startswith("Potentially sensitive content was detected")
    assert payload["due_outs"] == []
