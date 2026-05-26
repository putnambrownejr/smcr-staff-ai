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
    assert "sys-air-support-estimate" in ids
    assert "sys-air-ground-coordination-matrix" in ids
    assert "sys-aviation-supportability-matrix" in ids
    assert "sys-running-estimate" in ids
    assert "sys-orm-worksheet" in ids
    assert "sys-no-go-criteria" in ids
    assert "sys-residual-risk-decision-note" in ids
    assert "sys-rehearsal-safety-brief" in ids
    assert "sys-admin-estimate" in ids
    assert "sys-admin-task-tracker" in ids
    assert "sys-routing-matrix" in ids
    assert "sys-pre-drill-admin-readiness-check" in ids
    assert "sys-troop-flow-checklist" in ids
    assert "sys-formation-transition-matrix" in ids
    assert "sys-leader-touchpoint-plan" in ids
    assert "sys-synchronization-matrix" in ids
    assert "sys-decision-support-matrix" in ids
    assert "sys-due-out-tracker" in ids
    assert "sys-collection-matrix" in ids
    assert "sys-sustainment-matrix" in ids
    assert "sys-movement-table" in ids
    assert "sys-medical-estimate" in ids
    assert "sys-casevac-quick-card" in ids
    assert "sys-religious-support-plan" in ids
    assert "sys-rmt-support-matrix" in ids
    assert "sys-morale-welfare-estimate" in ids
    assert "sys-road-to-war-brief" in ids
    assert "sys-public-affairs-plan" in ids
    assert "sys-security-annex" in ids
    assert "sys-visitor-control-checklist" in ids
    assert "sys-traffic-parking-control-plan" in ids
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

    air_support_estimate = next(record for record in catalog.list() if record.template_id == "sys-air-support-estimate")
    assert air_support_estimate.template_type.value == "air_support_estimate"
    assert "aviation" in air_support_estimate.tags

    air_ground_coordination = next(
        record for record in catalog.list() if record.template_id == "sys-air-ground-coordination-matrix"
    )
    assert air_ground_coordination.template_type.value == "air_ground_coordination_matrix"
    assert "airo" in air_ground_coordination.tags

    aviation_supportability = next(
        record for record in catalog.list() if record.template_id == "sys-aviation-supportability-matrix"
    )
    assert aviation_supportability.template_type.value == "aviation_supportability_matrix"
    assert "ace" in aviation_supportability.tags

    orm_worksheet = next(record for record in catalog.list() if record.template_id == "sys-orm-worksheet")
    assert orm_worksheet.template_type.value == "orm_worksheet"
    assert "safety" in orm_worksheet.tags

    no_go_criteria = next(record for record in catalog.list() if record.template_id == "sys-no-go-criteria")
    assert no_go_criteria.template_type.value == "no_go_criteria"
    assert "orm" in no_go_criteria.tags

    residual_risk = next(
        record for record in catalog.list() if record.template_id == "sys-residual-risk-decision-note"
    )
    assert residual_risk.template_type.value == "residual_risk_decision_note"
    assert "safety" in residual_risk.tags

    rehearsal_safety_brief = next(
        record for record in catalog.list() if record.template_id == "sys-rehearsal-safety-brief"
    )
    assert rehearsal_safety_brief.template_type.value == "rehearsal_safety_brief"
    assert "orm" in rehearsal_safety_brief.tags

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

    troop_flow_checklist = next(record for record in catalog.list() if record.template_id == "sys-troop-flow-checklist")
    assert troop_flow_checklist.template_type.value == "troop_flow_checklist"
    assert "sel" in troop_flow_checklist.tags

    formation_transition_matrix = next(
        record for record in catalog.list() if record.template_id == "sys-formation-transition-matrix"
    )
    assert formation_transition_matrix.template_type.value == "formation_transition_matrix"
    assert "sel" in formation_transition_matrix.tags

    leader_touchpoint_plan = next(
        record for record in catalog.list() if record.template_id == "sys-leader-touchpoint-plan"
    )
    assert leader_touchpoint_plan.template_type.value == "leader_touchpoint_plan"
    assert "leadership" in leader_touchpoint_plan.tags

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

    movement_table = next(record for record in catalog.list() if record.template_id == "sys-movement-table")
    assert movement_table.template_type.value == "movement_table"
    assert "s4" in movement_table.tags

    medical_estimate = next(record for record in catalog.list() if record.template_id == "sys-medical-estimate")
    assert medical_estimate.template_type.value == "medical_estimate"
    assert "medical" in medical_estimate.tags

    casevac_quick_card = next(record for record in catalog.list() if record.template_id == "sys-casevac-quick-card")
    assert casevac_quick_card.template_type.value == "casevac_quick_card"
    assert "casevac" in casevac_quick_card.tags

    religious_support_plan = next(
        record for record in catalog.list() if record.template_id == "sys-religious-support-plan"
    )
    assert religious_support_plan.template_type.value == "religious_support_plan"
    assert "chaplain" in religious_support_plan.tags

    rmt_support_matrix = next(record for record in catalog.list() if record.template_id == "sys-rmt-support-matrix")
    assert rmt_support_matrix.template_type.value == "rmt_support_matrix"
    assert "rp" in rmt_support_matrix.tags

    morale_welfare_estimate = next(
        record for record in catalog.list() if record.template_id == "sys-morale-welfare-estimate"
    )
    assert morale_welfare_estimate.template_type.value == "morale_welfare_estimate"
    assert "welfare" in morale_welfare_estimate.tags

    road_to_war_brief = next(record for record in catalog.list() if record.template_id == "sys-road-to-war-brief")
    assert road_to_war_brief.template_type.value == "road_to_war_brief"
    assert "scenario" in road_to_war_brief.tags

    public_affairs_plan = next(record for record in catalog.list() if record.template_id == "sys-public-affairs-plan")
    assert public_affairs_plan.template_type.value == "public_affairs_plan"
    assert "pao" in public_affairs_plan.tags

    security_annex = next(record for record in catalog.list() if record.template_id == "sys-security-annex")
    assert security_annex.template_type.value == "security_annex"
    assert "security" in security_annex.tags

    visitor_control = next(record for record in catalog.list() if record.template_id == "sys-visitor-control-checklist")
    assert visitor_control.template_type.value == "visitor_control_checklist"
    assert "provost" in visitor_control.tags

    traffic_parking = next(
        record for record in catalog.list() if record.template_id == "sys-traffic-parking-control-plan"
    )
    assert traffic_parking.template_type.value == "traffic_parking_control_plan"
    assert "safety" in traffic_parking.tags

    resource_estimate = next(record for record in catalog.list() if record.template_id == "sys-resource-estimate")
    assert resource_estimate.template_type.value == "resource_estimate"
    assert "g8" in resource_estimate.tags

    inspection_readiness = next(
        record for record in catalog.list() if record.template_id == "sys-inspection-readiness-plan")
    assert inspection_readiness.template_type.value == "inspection_readiness_plan"
    assert "ig" in inspection_readiness.tags
