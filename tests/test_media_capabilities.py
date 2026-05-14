from fastapi.testclient import TestClient

from app.main import app


def test_data_merge_route_returns_similarity_candidates() -> None:
    client = TestClient(app)

    response = client.post(
        "/analysis/merge-records",
        json={
            "left_records": [
                {"record_id": "left-1", "fields": {"name": "Capt Example", "mos": "0602", "unit": "6th Comm Bn"}}
            ],
            "right_records": [
                {
                    "record_id": "right-1",
                    "fields": {"name": "Captain Example", "mos": "0602", "unit": "6th Comm Battalion"},
                }
            ],
            "compare_fields": ["name", "mos", "unit"],
            "similarity_threshold": 0.6,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_candidates"]
    assert payload["merged_rows"]


def test_tdg_route_returns_training_scaffold() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/tdg",
        json={
            "title": "Reserve convoy link-up",
            "theme": "small-unit decision-making under time pressure",
            "training_objective": "Practice tactical judgment and risk tradeoffs.",
            "references": ["MCDP 1 Warfighting", "MCDP 3 Tactics"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_points"]
    assert payload["discussion_questions"]
    assert payload["instructor_notes"]


def test_poam_route_returns_line_items() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff-products/poam",
        json={
            "title": "Drill support order POA&M",
            "higher_guidance": [
                "Establish reporting timeline for drill weekend support.",
                "Coordinate S-6 comm checks and S-4 logistics support.",
            ],
            "warfighting_functions": ["command and control", "logistics"],
            "staff_sections": ["S-3", "S-4", "S-6"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["line_items"]
    assert payload["review_points"]
