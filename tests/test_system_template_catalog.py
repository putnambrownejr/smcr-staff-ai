from pathlib import Path

from app.services.templates.system_template_catalog import SystemTemplateCatalog


def test_system_template_catalog_includes_baseline_staff_library() -> None:
    catalog = SystemTemplateCatalog.from_yaml(Path("data/seed/system_templates.example.yaml"))

    ids = {record.template_id for record in catalog.list()}

    assert "sys-cub-brief" in ids
    assert "sys-cpb" in ids
    assert "sys-opord" in ids
    assert "sys-warno" in ids
    assert "sys-frago" in ids
    assert "sys-conop" in ids
    assert "sys-sitrep" in ids
    assert "sys-running-estimate" in ids
    assert "sys-admin-estimate" in ids
    assert "sys-admin-task-tracker" in ids
    assert "sys-routing-matrix" in ids
    assert "sys-pre-drill-admin-readiness-check" in ids
    assert "sys-synchronization-matrix" in ids
    assert "sys-decision-support-matrix" in ids
    assert "sys-due-out-tracker" in ids
    assert "sys-collection-matrix" in ids
    assert "sys-sustainment-matrix" in ids
    assert "sys-medical-estimate" in ids
    assert "sys-public-affairs-plan" in ids
    assert "sys-security-annex" in ids
    assert "sys-resource-estimate" in ids
    assert "sys-inspection-readiness-plan" in ids
    assert "sys-aar" in ids
    assert "sys-ipb" in ids
    assert "sys-decision-brief" in ids
    assert "sys-command-update" in ids
    assert "sys-naval-letter" in ids
    assert "sys-memorandum" in ids
    assert "sys-endorsement" in ids

    cpb = next(record for record in catalog.list() if record.template_id == "sys-cpb")
    assert "Civil Preparation of the Battlespace" in cpb.template_name
    assert "civil_affairs" in cpb.tags

    ipb = next(record for record in catalog.list() if record.template_id == "sys-ipb")
    assert ipb.template_type.value == "ipb"
    assert "s2" in ipb.tags
    assert ipb.preferred_format == "intelligence_estimate"

    running_estimate = next(record for record in catalog.list() if record.template_id == "sys-running-estimate")
    assert running_estimate.template_type.value == "running_estimate"
    assert "staff" in running_estimate.tags
    assert running_estimate.preferred_format == "estimate"

    admin_estimate = next(record for record in catalog.list() if record.template_id == "sys-admin-estimate")
    assert admin_estimate.template_type.value == "admin_estimate"
    assert "s1" in admin_estimate.tags

    admin_task_tracker = next(record for record in catalog.list() if record.template_id == "sys-admin-task-tracker")
    assert admin_task_tracker.template_type.value == "admin_task_tracker"
    assert "admin" in admin_task_tracker.tags

    routing_matrix = next(record for record in catalog.list() if record.template_id == "sys-routing-matrix")
    assert routing_matrix.template_type.value == "routing_matrix"
    assert "s1" in routing_matrix.tags

    pre_drill_admin = next(
        record for record in catalog.list() if record.template_id == "sys-pre-drill-admin-readiness-check"
    )
    assert pre_drill_admin.template_type.value == "pre_drill_admin_readiness_check"
    assert "admin" in pre_drill_admin.tags

    decision_support_matrix = next(
        record for record in catalog.list() if record.template_id == "sys-decision-support-matrix"
    )
    assert decision_support_matrix.template_type.value == "decision_support_matrix"
    assert "xo" in decision_support_matrix.tags

    due_out_tracker = next(record for record in catalog.list() if record.template_id == "sys-due-out-tracker")
    assert due_out_tracker.template_type.value == "due_out_tracker"
    assert "command_cell" in due_out_tracker.tags

    collection_matrix = next(record for record in catalog.list() if record.template_id == "sys-collection-matrix")
    assert collection_matrix.template_type.value == "collection_matrix"
    assert "s2" in collection_matrix.tags

    sustainment_matrix = next(record for record in catalog.list() if record.template_id == "sys-sustainment-matrix")
    assert sustainment_matrix.template_type.value == "sustainment_matrix"
    assert "logistics" in sustainment_matrix.tags

    medical_estimate = next(record for record in catalog.list() if record.template_id == "sys-medical-estimate")
    assert medical_estimate.template_type.value == "medical_estimate"
    assert "medical" in medical_estimate.tags

    public_affairs_plan = next(record for record in catalog.list() if record.template_id == "sys-public-affairs-plan")
    assert public_affairs_plan.template_type.value == "public_affairs_plan"
    assert "pao" in public_affairs_plan.tags

    security_annex = next(record for record in catalog.list() if record.template_id == "sys-security-annex")
    assert security_annex.template_type.value == "security_annex"
    assert "security" in security_annex.tags

    resource_estimate = next(record for record in catalog.list() if record.template_id == "sys-resource-estimate")
    assert resource_estimate.template_type.value == "resource_estimate"
    assert "g8" in resource_estimate.tags

    inspection_readiness = next(
        record for record in catalog.list() if record.template_id == "sys-inspection-readiness-plan")
    assert inspection_readiness.template_type.value == "inspection_readiness_plan"
    assert "ig" in inspection_readiness.tags
