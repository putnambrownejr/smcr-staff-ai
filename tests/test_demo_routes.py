from fastapi.testclient import TestClient

from app.main import app


def test_demo_status_lists_repo_mode_routes() -> None:
    client = TestClient(app)

    response = client.get("/demo/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "stateless_demo"
    assert "/demo/chief/brief" in payload["routes"]


def test_demo_chief_brief_returns_digest_fields() -> None:
    client = TestClient(app)

    response = client.get("/demo/chief/brief")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_key"] == "demo-smcr-officer"
    assert payload["summary_lines"]
    assert payload["top_priority_items"]


def test_demo_staff_product_draft_works_without_local_state() -> None:
    client = TestClient(app)

    response = client.post(
        "/demo/staff-products/draft",
        json={
            "product_type": "warno",
            "topic": "Training-only drill weekend field exercise",
            "training_or_fictional": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_type"] == "warno"
    assert payload["sections"]
