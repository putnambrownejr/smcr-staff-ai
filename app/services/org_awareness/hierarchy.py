import json
from pathlib import Path

from app.schemas.org import OrgUnit


class OrgHierarchyService:
    def __init__(self, units: list[OrgUnit]) -> None:
        self.units = {unit.unit_id: unit for unit in units}

    @classmethod
    def from_json(cls, path: str | Path) -> "OrgHierarchyService":
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls([OrgUnit.model_validate(item) for item in payload["units"]])

    def list_units(self) -> list[OrgUnit]:
        return list(self.units.values())

    def parent_of(self, unit_id: str) -> OrgUnit | None:
        unit = self.units.get(unit_id)
        if unit is None or unit.higher_headquarters_id is None:
            return None
        return self.units.get(unit.higher_headquarters_id)

    def children_of(self, unit_id: str) -> list[OrgUnit]:
        return [unit for unit in self.units.values() if unit.higher_headquarters_id == unit_id]

    def chain_to_root(self, unit_id: str) -> list[OrgUnit]:
        chain: list[OrgUnit] = []
        current = self.units.get(unit_id)
        seen: set[str] = set()
        while current is not None and current.unit_id not in seen:
            chain.append(current)
            seen.add(current.unit_id)
            current = self.parent_of(current.unit_id)
        return chain
