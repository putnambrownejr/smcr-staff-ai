from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.bench_sections import get_bench_sections_store
from app.main import app
from app.services.staff.bench_sections_store import BenchSectionsStore


def test_bench_sections_routes(tmp_path: Path) -> None:
    store = BenchSectionsStore(tmp_path / "bench-sections")

    def override_store() -> BenchSectionsStore:
        return store

    app.dependency_overrides[get_bench_sections_store] = override_store
    client = TestClient(app)
    try:
        missing_response = client.get("/bench-sections/capt-bench")
        assert missing_response.status_code == 404

        put_response = client.put(
            "/bench-sections/capt-bench",
            json={"sections": [" S-1/Admin ", "S-3"]},
        )
        assert put_response.status_code == 200
        put_payload = put_response.json()
        assert put_payload["config"]["sections"] == ["S-1/Admin", "S-3"]
        assert put_payload["message"]

        get_response = client.get("/bench-sections/capt-bench")
        assert get_response.status_code == 200
        assert get_response.json()["sections"] == ["S-1/Admin", "S-3"]

        delete_response = client.delete("/bench-sections/capt-bench")
        assert delete_response.status_code == 204
        assert not delete_response.content

        empty_response = client.put(
            "/bench-sections/capt-bench",
            json={"sections": []},
        )
        assert empty_response.status_code == 422
    finally:
        app.dependency_overrides.clear()
