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
