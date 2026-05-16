from datetime import UTC, datetime
from pathlib import Path

from app.core.config import default_local_context_dir
from app.schemas.source_updates import (
    DocumentationUpdateCandidate,
    DocumentationUpdateStatusUpdate,
    UpdateReviewStatus,
)


class DocumentUpdateStore:
    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.root_dir = Path(root_dir or (default_local_context_dir() / "document_updates"))
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save_many(self, candidates: list[DocumentationUpdateCandidate]) -> list[DocumentationUpdateCandidate]:
        saved: list[DocumentationUpdateCandidate] = []
        for candidate in candidates:
            existing = self.get(candidate.candidate_id)
            if existing is not None:
                candidate.review_status = existing.review_status
                candidate.reviewed_at = existing.reviewed_at
                candidate.review_notes = existing.review_notes
            self._path(candidate.candidate_id).write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
            saved.append(candidate)
        return saved

    def list(self, status: UpdateReviewStatus | None = None) -> list[DocumentationUpdateCandidate]:
        records = [
            DocumentationUpdateCandidate.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob("*.json"))
        ]
        if status is not None:
            records = [record for record in records if record.review_status == status]
        return sorted(records, key=lambda record: record.detected_at, reverse=True)

    def get(self, candidate_id: str) -> DocumentationUpdateCandidate | None:
        path = self._path(candidate_id)
        if not path.exists():
            return None
        return DocumentationUpdateCandidate.model_validate_json(path.read_text(encoding="utf-8"))

    def update_status(
        self,
        candidate_id: str,
        update: DocumentationUpdateStatusUpdate,
    ) -> DocumentationUpdateCandidate | None:
        candidate = self.get(candidate_id)
        if candidate is None:
            return None
        candidate.review_status = update.review_status
        candidate.review_notes = update.review_notes
        if update.review_status != UpdateReviewStatus.new:
            candidate.reviewed_at = datetime.now(UTC)
        self._path(candidate_id).write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
        return candidate

    def _path(self, candidate_id: str) -> Path:
        safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in candidate_id)
        return self.root_dir / f"{safe_id}.json"
