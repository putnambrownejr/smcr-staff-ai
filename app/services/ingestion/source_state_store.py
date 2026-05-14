from __future__ import annotations

from pathlib import Path

from app.schemas.source_state import VerifiedSourceState


class SourceStateStore:
    def __init__(self, root_dir: str | Path = "data/local_context/source_states") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: VerifiedSourceState) -> VerifiedSourceState:
        self._path(state.source_state_id).write_text(state.model_dump_json(indent=2), encoding="utf-8")
        return state

    def list(self) -> list[VerifiedSourceState]:
        records = [
            VerifiedSourceState.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob("*.json"))
        ]
        return sorted(records, key=lambda record: record.last_verified_at, reverse=True)

    def get(self, source_state_id: str) -> VerifiedSourceState | None:
        path = self._path(source_state_id)
        if not path.exists():
            return None
        return VerifiedSourceState.model_validate_json(path.read_text(encoding="utf-8"))

    def _path(self, source_state_id: str) -> Path:
        safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in source_state_id)
        return self.root_dir / f"{safe_id}.json"
