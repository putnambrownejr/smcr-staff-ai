from fastapi.testclient import TestClient

from app.main import app


def test_verify_sources_returns_manifest_summary() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/verify-sources",
        json={"manifest_path": "data/seed/doctrine_manifest.example.yaml"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["manifest_validation"] is not None
    assert payload["summary_lines"]


def test_verify_sources_flags_tag_page_only_refs() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/verify-sources",
        json={
            "refs": [
                {
                    "title": "Training tag page",
                    "url": "https://www.marines.mil/News/Publications/MCPEL/Tag/285311/training-and-readiness/",
                    "verification_status": "tag_page_only",
                    "classification_label": "UNCLASSIFIED",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["findings"][0]["warnings"]


def test_verify_sources_rejects_absolute_local_paths() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/verify-sources",
        json={"manifest_path": "C:\\Windows\\win.ini"},
    )

    assert response.status_code == 404
    assert "Absolute local paths are not allowed" in response.json()["detail"]
