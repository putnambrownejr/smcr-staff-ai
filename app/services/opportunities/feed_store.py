from pathlib import Path

from app.schemas.career_opportunities import (
    CareerOpportunitySourceState,
    OpportunitySourceKey,
)


class CareerOpportunityFeedStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: CareerOpportunitySourceState) -> CareerOpportunitySourceState:
        path = self._path(state.source.key)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)
        return state

    def get(self, source_key: OpportunitySourceKey) -> CareerOpportunitySourceState | None:
        path = self._path(source_key)
        if not path.exists():
            return None
        return CareerOpportunitySourceState.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[CareerOpportunitySourceState]:
        return [
            CareerOpportunitySourceState.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob("*.json"))
        ]

    def _path(self, source_key: OpportunitySourceKey) -> Path:
        return self.root_dir / f"{source_key.value}.json"
