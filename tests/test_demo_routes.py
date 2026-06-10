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


def test_demo_staff_planning_package_post_returns_cross_staff_example() -> None:
    client = TestClient(app)

    response = client.post(
        "/demo/planning/staff-package",
        json={
            "title": "Demo drill prep",
            "event_type": "drill",
            "mission_or_training_goal": "Prepare a reserve drill support package.",
            "coordinating_sections": ["S-1", "S-4", "S-6"],
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Staff planning package: Demo drill prep"
    assert payload["s1_readiness"]["admin_task_tracker"]


def test_demo_maradmin_feed_returns_stateless_records() -> None:
    client = TestClient(app)

    response = client.get("/demo/maradmins/feed")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["source_family"] == "MARADMIN"
    assert "Reserve" in payload[0]["tags"]


def test_demo_dts_helper_returns_admin_workflow() -> None:
    client = TestClient(app)

    response = client.post(
        "/demo/staff/s1/dts-helper",
        json={
            "title": "June drill travel authorization",
            "facts": ["Traveler needs lodging for drill weekend."],
            "constraints": ["Route before Friday."],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_type"] == "dts_authorization"
    assert payload["checklist"]
    assert payload["required_documents"]


def test_demo_billet_recommendations_return_scored_matches() -> None:
    client = TestClient(app)

    response = client.post(
        "/demo/billets/recommend",
        json={
            "profile": {
                "mos": "0602",
                "rank": "Capt",
                "desired_locations": ["Fort Worth"],
                "keywords": ["communications"],
                "willing_to_travel": True,
            },
            "max_results": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["billets_seen"] >= 1
    assert payload["recommendations"]
    assert payload["recommendations"][0]["billet"]["title"] == "Communications Officer"
