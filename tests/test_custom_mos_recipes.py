from fastapi.testclient import TestClient

from app.api.routes.custom_mos_recipes import _get_store
from app.main import app
from app.services.staff.custom_mos_store import CustomMosRecipeStoreService


def _override_store(tmp_path):
    store = CustomMosRecipeStoreService(tmp_path / "custom-mos-recipes")
    app.dependency_overrides[_get_store] = lambda: store
    return store


def test_create_and_list_custom_mos_recipe(tmp_path) -> None:
    _override_store(tmp_path)
    client = TestClient(app)
    try:
        response = client.post(
            "/custom-mos-recipes/test-user",
            json={
                "mos_code": "1302",
                "title": "Combat Engineer Officer",
                "parent_agent": "staff-opso",
                "focus_areas": ["obstacle planning", "mobility/counter-mobility"],
                "starter_prompt": "Help me shape an engineer support plan.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recipes"]) == 1
        assert data["recipes"][0]["mos_code"] == "1302"
        assert data["recipes"][0]["parent_agent"] == "staff-opso"

        list_response = client.get("/custom-mos-recipes/test-user")
        assert list_response.status_code == 200
        assert len(list_response.json()["recipes"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_upsert_replaces_existing_mos_code(tmp_path) -> None:
    _override_store(tmp_path)
    client = TestClient(app)
    try:
        client.post(
            "/custom-mos-recipes/test-user",
            json={
                "mos_code": "0602",
                "title": "Comms Officer v1",
                "parent_agent": "staff-s6",
                "focus_areas": ["PACE planning"],
            },
        )
        response = client.post(
            "/custom-mos-recipes/test-user",
            json={
                "mos_code": "0602",
                "title": "Comms Officer v2",
                "parent_agent": "staff-s6",
                "focus_areas": ["PACE planning", "crypto accountability"],
            },
        )
        assert response.status_code == 200
        recipes = response.json()["recipes"]
        assert len(recipes) == 1
        assert recipes[0]["title"] == "Comms Officer v2"
        assert len(recipes[0]["focus_areas"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_delete_custom_mos_recipe(tmp_path) -> None:
    _override_store(tmp_path)
    client = TestClient(app)
    try:
        client.post(
            "/custom-mos-recipes/test-user",
            json={
                "mos_code": "1302",
                "title": "Engineer",
                "parent_agent": "staff-opso",
                "focus_areas": ["breaching"],
            },
        )
        response = client.delete("/custom-mos-recipes/test-user/1302")
        assert response.status_code == 200
        assert len(response.json()["recipes"]) == 0
    finally:
        app.dependency_overrides.clear()


def test_invalid_parent_agent_rejected(tmp_path) -> None:
    _override_store(tmp_path)
    client = TestClient(app)
    try:
        response = client.post(
            "/custom-mos-recipes/test-user",
            json={
                "mos_code": "9999",
                "title": "Fake",
                "parent_agent": "nonexistent-agent",
                "focus_areas": ["nothing"],
            },
        )
        assert response.status_code == 400
        assert "Invalid parent_agent" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_empty_user_key_returns_empty(tmp_path) -> None:
    _override_store(tmp_path)
    client = TestClient(app)
    try:
        response = client.get("/custom-mos-recipes/fresh-user")
        assert response.status_code == 200
        assert response.json()["recipes"] == []
    finally:
        app.dependency_overrides.clear()
