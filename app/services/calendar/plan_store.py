from pathlib import Path

from app.schemas.calendar import DrillPrepPlanResponse


class DrillPrepPlanStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(self, plan: DrillPrepPlanResponse) -> DrillPrepPlanResponse:
        self._path(plan.id).write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        return plan

    def get(self, plan_id: str) -> DrillPrepPlanResponse | None:
        path = self._path(plan_id)
        if not path.exists():
            return None
        return DrillPrepPlanResponse.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[DrillPrepPlanResponse]:
        plans = [
            DrillPrepPlanResponse.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob("*.json"))
        ]
        return sorted(plans, key=lambda plan: plan.drill_date)

    def delete(self, plan_id: str) -> bool:
        path = self._path(plan_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _path(self, plan_id: str) -> Path:
        safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in plan_id)
        return self.root_dir / f"{safe_id}.json"
