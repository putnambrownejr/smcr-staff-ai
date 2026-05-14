from fastapi.testclient import TestClient

from app.main import app


def test_personnel_product_builder_supports_fitrep_planning() -> None:
    client = TestClient(app)

    response = client.post(
        "/personnel/products",
        json={
            "product_type": "fitrep_planning",
            "title": "Annual FitRep prep",
            "subject_name": "Capt Example",
            "occasion": "Annual",
            "facts": ["Served as battalion CommO during AT planning cycle"],
            "achievements": ["Built a reserve communications tracker"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_type"] == "fitrep_planning"
    assert payload["sections"]
    assert any("MCO 1610.7" in citation for citation in payload["citations"])
    assert payload["routing_steps"]


def test_personnel_product_builder_supports_routing_package() -> None:
    client = TestClient(app)

    response = client.post(
        "/personnel/products",
        json={
            "product_type": "routing_package",
            "title": "Decision routing package",
            "routing_chain": ["action officer", "XO", "CO"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["required_documents"]
    assert any("correspondence manual" in citation.lower() for citation in payload["citations"])
