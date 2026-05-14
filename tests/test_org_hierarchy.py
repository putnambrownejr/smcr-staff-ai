from pathlib import Path

from app.services.org_awareness.hierarchy import OrgHierarchyService


def test_org_hierarchy_chain_lookup_works() -> None:
    service = OrgHierarchyService.from_json(Path("data/seed/org_units.example.json"))
    chain = service.chain_to_root("example-supported-company")

    assert [unit.unit_id for unit in chain] == [
        "example-supported-company",
        "example-1-25",
        "example-25th-marines",
        "4th-mardiv",
        "marforres",
    ]
