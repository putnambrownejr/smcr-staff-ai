from fastapi.testclient import TestClient

from app.main import app

STEPS = [
    "area-study-builder",
    "actor-network-analyst",
    "information-requirements-manager",
    "ipb-assistant",
]


def test_source_aware_specialist_chain_forwards_prior_assessments() -> None:
    response = TestClient(app).post("/agents/chain", json={"scenario": "Training scenario", "steps": [{"agent_id": agent_id} for agent_id in STEPS]})

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert [row["agent_id"] for row in data["results"]] == STEPS
    assert [row["scenario_output"]["role"] for row in data["results"]] == [
        "area_study", "actor_network", "information_requirements", "ipb"
    ]
    assert "Area study: received" in data["results"][-1]["response"]["answer"]
