from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.user_profile import get_user_profile_store
from app.main import app
from app.services.staff.user_profile_store import UserProfileStore


def test_user_profile_routes(tmp_path: Path) -> None:
    store = UserProfileStore(tmp_path / "user-profiles")

    def override_store() -> UserProfileStore:
        return store

    app.dependency_overrides[get_user_profile_store] = override_store
    client = TestClient(app)
    try:
        # 404 when no profile exists
        missing = client.get("/user-profile/capt-bench")
        assert missing.status_code == 404

        # PUT creates profile
        put_response = client.put(
            "/user-profile/capt-bench",
            json={
                "billet": "SuppO",
                "unit": "3rd Bn 14th Marines",
                "mos": "0402",
                "format_preference": "naval_letter",
                "one_number_one_rule": True,
                "style_notes": "Keep it concise.",
            },
        )
        assert put_response.status_code == 200
        payload = put_response.json()
        assert payload["profile"]["billet"] == "SuppO"
        assert payload["profile"]["mos"] == "0402"
        assert payload["message"]

        # GET returns stored profile
        get_response = client.get("/user-profile/capt-bench")
        assert get_response.status_code == 200
        assert get_response.json()["billet"] == "SuppO"

        # DELETE removes profile
        delete_response = client.delete("/user-profile/capt-bench")
        assert delete_response.status_code == 204
        assert not delete_response.content

        # GET returns 404 after delete
        after_delete = client.get("/user-profile/capt-bench")
        assert after_delete.status_code == 404

    finally:
        app.dependency_overrides.clear()
