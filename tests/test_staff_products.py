from fastapi.testclient import TestClient

from app.main import app
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.services.staff_products.builder import StaffProductBuilder


def test_staff_product_builder_creates_opord_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.opord,
            topic="Training-only field exercise",
            facts=["Annual training timeline is tentative."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Situation" in headings
    assert "5. Command and Signal" in headings
    assert response.review_checklist
    assert response.structured_citations


def test_staff_products_draft_route_supports_correspondence() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff-products/draft",
        json={
            "product_type": "memorandum",
            "topic": "Training-only staff package routing",
            "audience": "Battalion staff",
            "facts": ["Use current correspondence manual."],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_type"] == "memorandum"
    assert any("5216.5" in citation["title"] for citation in payload["structured_citations"])


def test_staff_product_builder_creates_conop_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.conop,
            topic="Initial company concept for field training",
            facts=["Subordinate elements must refine local concepts."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Purpose and End State" in headings
    assert "2. Unit and Sub-Unit Relationships" in headings
    assert response.review_checklist
