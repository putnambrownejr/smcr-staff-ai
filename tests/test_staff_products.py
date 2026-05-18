from fastapi.testclient import TestClient

from app.main import app
from app.schemas.product_templates import ProductTemplateRecord, ProductTemplateType
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
    assert payload["formatting_notes"]


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


def test_staff_product_builder_adds_navmac_style_notes_for_naval_letter() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.naval_letter,
            topic="Training-only command package routing",
            facts=["Use current correspondence guidance."],
        )
    )

    assert response.formatting_notes
    assert any("From/To/Via/Subj" in note for note in response.formatting_notes)


def test_staff_product_builder_strengthens_aar_sections_and_notes() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.aar,
            topic="Training-only field exercise AAR",
            facts=["Unit measured reporting discipline and accountability under friction."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Event and Command Frame" in headings
    assert "3. Sustains and What Held" in headings
    assert "5. Corrective Actions for the Next Event" in headings
    assert any("XO or S-3 would keep" in note for note in response.formatting_notes)
    assert any("named owner" in item for item in response.review_checklist)
    assert any("1553.3C" in citation.title for citation in response.structured_citations)


def test_staff_product_builder_creates_decision_brief_slide_structure() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.decision_brief,
            topic="Decision brief for reserve field training scope reduction",
            facts=["Commander must decide whether to keep two lanes or cut to one."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "Slide 1. Commander Problem and Decision Required" in headings
    assert "Slide 4. Options or COAs" in headings
    assert any("one decision problem" in note for note in response.formatting_notes)
    assert any("Cut any slide" in item for item in response.review_checklist)


def test_staff_product_builder_applies_local_template_guidance() -> None:
    template = ProductTemplateRecord(
        template_id="abc12345def67890",
        template_name="Example CUB",
        template_type=ProductTemplateType.cub_brief,
        reusable_headings=["Executive Snapshot", "Friction", "Decision Required"],
        reusable_guidance=["Keep the brief to five slides and lead with friction."],
        audience_hint="Battalion commander",
    )

    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.command_update_brief,
            topic="Weekly reserve readiness update",
        ),
        templates=[template],
    )

    assert response.applied_templates == ["Example CUB"]
    assert any("local example template was applied" in note.lower() for note in response.formatting_notes)
    assert any("stale names" in item for item in response.review_checklist)
    assert any("Local template reference" in prompt for prompt in response.sections[0].prompts)


def test_staff_products_agent_defaults_slide_requests_to_decision_brief() -> None:
    from app.services.agents.base import AgentContext
    from app.services.agents.staff_products_agent import build_staff_products_agent

    agent = build_staff_products_agent()
    response = agent.run(
        "Build me a short slide deck for a commander decision on drill weekend field training scope.",
        context=AgentContext(),
    )

    assert "DECISION_BRIEF draft scaffold" in response.answer
