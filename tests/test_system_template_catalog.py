from pathlib import Path

from app.services.templates.system_template_catalog import SystemTemplateCatalog

DETAIL_DIR = Path("data/seed/system_templates")

CURATED_IDS = {
    "sys-opord",
    "sys-warno",
    "sys-frago",
    "sys-conop",
    "sys-decision-brief",
    "sys-command-update",
    "sys-aar",
    "sys-naval-letter",
}


def test_system_template_catalog_lists_only_curated_templates() -> None:
    catalog = SystemTemplateCatalog.from_dir(DETAIL_DIR)

    ids = {record.template_id for record in catalog.list()}

    assert ids == CURATED_IDS
    # Retired thin templates must no longer appear.
    assert "sys-cpb" not in ids
    assert "sys-ipb" not in ids
    assert "sys-memorandum" not in ids

    opord = catalog.get("sys-opord")
    assert opord is not None
    assert opord.template_type.value == "opord"


def test_system_template_catalog_exposes_built_out_detail() -> None:
    catalog = SystemTemplateCatalog.from_dir(DETAIL_DIR)

    detail = catalog.get_detail("sys-opord")

    assert detail is not None
    assert detail.template_name == "Operations Order (OPORD)"
    assert detail.template_type.value == "opord"
    # Curated templates are served by the content API, not a static .md file.
    assert detail.source_path == "/product-templates/system/sys-opord"
    assert detail.agent_handoff == "staff-products"
    assert detail.one_liner
    assert detail.when_to_use
    assert detail.doctrine_refs
    assert detail.sections[0].heading == "Task Organization"
    assert detail.sections[0].scaffold
    assert detail.sections[0].example


def test_system_template_catalog_detail_for_every_curated_template() -> None:
    catalog = SystemTemplateCatalog.from_dir(DETAIL_DIR)

    for template_id in CURATED_IDS:
        detail = catalog.get_detail(template_id)
        assert detail is not None, template_id
        assert detail.sections, f"{template_id} has no sections"
        # Every section carries an annotated scaffold and a worked example.
        for section in detail.sections:
            assert section.scaffold, f"{template_id}/{section.key} missing scaffold"
            assert section.example, f"{template_id}/{section.key} missing example"


def test_system_template_catalog_returns_none_for_unknown() -> None:
    catalog = SystemTemplateCatalog.from_dir(DETAIL_DIR)

    assert catalog.get("sys-does-not-exist") is None
    assert catalog.get_detail("sys-does-not-exist") is None
