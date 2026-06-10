from fastapi.testclient import TestClient

from app.main import app


def test_admin_workflow_builder_supports_dts_and_orders() -> None:
    client = TestClient(app)

    response = client.post(
        "/admin/workflow",
        json={
            "workflow_type": "dts_voucher",
            "title": "Post-drill voucher",
            "facts": ["Receipts are complete"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["required_documents"]
    assert any("receipts" in item.lower() for item in payload["required_documents"])


def test_admin_workflow_builder_supports_gtcc() -> None:
    client = TestClient(app)

    response = client.post(
        "/admin/workflow",
        json={
            "workflow_type": "gtcc",
            "title": "Travel card follow-up",
            "facts": ["Voucher is pending"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert any("gtcc" in item.lower() or "travel-card" in item.lower() for item in payload["checklist"])


def test_staff_s1_mrows_rebuttal_route_returns_policy_rebuttal_scaffold() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/s1/mrows-rebuttal",
        json={
            "title": "Baggage reimbursement rebuttal",
            "facts": ["Baggage was required for orders-supported travel."],
            "constraints": ["Admin denied without a written citation."],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_type"] == "mrows_rebuttal"
    assert any("020204" in item for item in payload["checklist"])
    assert any("cited authority" in item.lower() for item in payload["review_points"])


def test_staff_s1_ridt_route_returns_delay_of_training_scaffold() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/s1/ridt",
        json={
            "title": "Missed drill request",
            "facts": ["Occupational conflict affects the scheduled drill weekend."],
            "constraints": ["Commander endorsement required before submission."],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_type"] == "ridt"
    assert any("reason code" in item.lower() for item in payload["checklist"])
    assert any("commander endorsement" in item.lower() for item in payload["required_documents"])
