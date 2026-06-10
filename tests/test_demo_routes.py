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


def test_demo_actions_returns_stateless_action_records() -> None:
    client = TestClient(app)

    response = client.get("/demo/actions")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["owner"]
    assert payload[0]["suspense_date"]
    assert payload[0]["history"]


def test_demo_handoff_returns_stateless_continuity_context() -> None:
    client = TestClient(app)

    response = client.get("/demo/handoffs/demo-smcr-officer")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_key"] == "demo-smcr-officer"
    assert payload["admin_watch_items"]
    assert payload["warnings"]


def test_demo_staff_planning_package_returns_cross_staff_example() -> None:
    client = TestClient(app)

    response = client.get("/demo/planning/staff-package")

    assert response.status_code == 200
    payload = response.json()
    assert payload["planning_approach"]["recommended_method"] in {"mcpp", "r2p2"}
    assert payload["s1_readiness"]["admin_task_tracker"]
    assert payload["product_package"]
