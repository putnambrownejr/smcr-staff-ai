from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.product_templates import get_context_store
from app.api.routes.product_templates import get_template_repository as get_product_template_repository
from app.api.routes.staff_products import get_template_repository as get_staff_product_template_repository
from app.main import app
from app.schemas.product_templates import CreateProductTemplateFromContextRequest, ProductTemplateType
from app.services.storage.local_context_store import LocalContextStore
from app.services.templates.product_template_repository import ProductTemplateRepository


def test_product_template_repository_promotes_local_example(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    source = context_store.save(
        filename="civil-prep-battlespace-example.md",
        content=(
            b"# Civil Preparation of the Battlespace\n\n## ASCOPE Factors\n- Placeholder\n\n"
            b"## Civil Actors\n- Placeholder\n\n"
            b"## Civil Information Gaps\n"
        ),
        content_type="text/markdown",
        document_type="product_example",
        tags=["civil-affairs", "g9"],
    )
    repository = ProductTemplateRepository(tmp_path / "templates")

    record = repository.create_from_context(
        request=CreateProductTemplateFromContextRequest(
            context_id=source.context_id,
            template_name="Civil Affairs CPB Example",
            template_type=ProductTemplateType.cpb,
        ),
        context_store=context_store,
    )

    assert record.source_context_id == source.context_id
    assert record.template_type.value == "cpb"
    assert "ASCOPE Factors" in record.reusable_headings
    assert record.reusable_headings
    assert record.local_only is True


def test_product_template_routes_create_list_and_reuse(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    repository = ProductTemplateRepository(tmp_path / "templates")
    source = context_store.save(
        filename="frago-example.md",
        content=b"CHANGES:\nTask 1\n\nTASKS:\nTask 2\n\nCOORDINATING INSTRUCTIONS:\nTask 3\n",
        content_type="text/markdown",
        document_type="product_example",
    )

    app.dependency_overrides[get_context_store] = lambda: context_store
    app.dependency_overrides[get_product_template_repository] = lambda: repository
    app.dependency_overrides[get_staff_product_template_repository] = lambda: repository
    client = TestClient(app)
    try:
        create_response = client.post(
            "/product-templates/from-context",
            json={
                "context_id": source.context_id,
                "template_name": "Company FRAGO Example",
                "template_type": "frago",
                "tags": ["ops"],
            },
        )
        assert create_response.status_code == 200
        template_id = create_response.json()["template_id"]

        list_response = client.get("/product-templates")
        assert list_response.status_code == 200
        assert list_response.json()["total_templates"] == 1

        draft_response = client.post(
            "/staff-products/draft",
            json={
                "product_type": "frago",
                "topic": "Training-only adjustment for field-lane timeline",
                "template_ids": [template_id],
            },
        )
        assert draft_response.status_code == 200
        payload = draft_response.json()
        assert payload["applied_templates"] == ["Company FRAGO Example"]
        first_section_prompts = payload["sections"][0]["prompts"]
        assert any("Local template reference" in prompt for prompt in first_section_prompts)
    finally:
        app.dependency_overrides.clear()


def test_product_template_running_estimate_type_is_supported() -> None:
    assert ProductTemplateType.running_estimate.value == "running_estimate"


def test_product_template_new_matrix_and_estimate_types_are_supported() -> None:
    assert ProductTemplateType.air_support_estimate.value == "air_support_estimate"
    assert ProductTemplateType.air_ground_coordination_matrix.value == "air_ground_coordination_matrix"
    assert ProductTemplateType.aviation_supportability_matrix.value == "aviation_supportability_matrix"
    assert ProductTemplateType.public_affairs_plan.value == "public_affairs_plan"
    assert ProductTemplateType.security_annex.value == "security_annex"
    assert ProductTemplateType.visitor_control_checklist.value == "visitor_control_checklist"
    assert ProductTemplateType.traffic_parking_control_plan.value == "traffic_parking_control_plan"
    assert ProductTemplateType.orm_worksheet.value == "orm_worksheet"
    assert ProductTemplateType.no_go_criteria.value == "no_go_criteria"
    assert ProductTemplateType.residual_risk_decision_note.value == "residual_risk_decision_note"
    assert ProductTemplateType.rehearsal_safety_brief.value == "rehearsal_safety_brief"
    assert ProductTemplateType.admin_estimate.value == "admin_estimate"
    assert ProductTemplateType.admin_task_tracker.value == "admin_task_tracker"
    assert ProductTemplateType.routing_matrix.value == "routing_matrix"
    assert ProductTemplateType.pre_drill_admin_readiness_check.value == "pre_drill_admin_readiness_check"
    assert ProductTemplateType.troop_flow_checklist.value == "troop_flow_checklist"
    assert ProductTemplateType.formation_transition_matrix.value == "formation_transition_matrix"
    assert ProductTemplateType.leader_touchpoint_plan.value == "leader_touchpoint_plan"
    assert ProductTemplateType.resource_estimate.value == "resource_estimate"
    assert ProductTemplateType.inspection_readiness_plan.value == "inspection_readiness_plan"
    assert ProductTemplateType.synchronization_matrix.value == "synchronization_matrix"
    assert ProductTemplateType.decision_support_matrix.value == "decision_support_matrix"
    assert ProductTemplateType.due_out_tracker.value == "due_out_tracker"
    assert ProductTemplateType.collection_matrix.value == "collection_matrix"
    assert ProductTemplateType.sustainment_matrix.value == "sustainment_matrix"
    assert ProductTemplateType.movement_table.value == "movement_table"
    assert ProductTemplateType.medical_estimate.value == "medical_estimate"
    assert ProductTemplateType.casevac_quick_card.value == "casevac_quick_card"
    assert ProductTemplateType.religious_support_plan.value == "religious_support_plan"
    assert ProductTemplateType.rmt_support_matrix.value == "rmt_support_matrix"
    assert ProductTemplateType.morale_welfare_estimate.value == "morale_welfare_estimate"
    assert ProductTemplateType.road_to_war_brief.value == "road_to_war_brief"
