from fastapi.testclient import TestClient

from app.public_library.app import RequestLimiter, create_app
from app.public_library.settings import PublicSettings


def test_bucket_refills_without_rejection_extending_wait() -> None:
    now = [0.0]
    bucket = RequestLimiter(2, 2, lambda: now[0])
    assert [bucket.retry_after() for _ in range(3)] == [0, 0, 1]
    now[0] = 0.25
    assert bucket.retry_after() == 1
    now[0] = 0.5
    assert bucket.retry_after() == 0
    now[0] = 100
    assert [bucket.retry_after() for _ in range(3)] == [0, 0, 1]


def test_mcp_and_web_share_bucket_but_health_remains_available() -> None:
    app = create_app(PublicSettings(request_burst=1, requests_per_second=0.001))
    with TestClient(app, base_url="http://127.0.0.1:8010") as client:
        assert client.get("/api/catalog").status_code == 200
        rejected = client.post("/mcp", headers={"X-Forwarded-For": "192.0.2.10"})
        assert rejected.status_code == 429
        assert int(rejected.headers["Retry-After"]) > 0
        assert rejected.headers["Cache-Control"] == "no-store"
        assert "Content-Security-Policy" in rejected.headers
        assert client.get("/", headers={"X-Forwarded-For": "192.0.2.20"}).status_code == 429
        assert client.get("/health").status_code == 200
