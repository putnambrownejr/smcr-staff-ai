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
