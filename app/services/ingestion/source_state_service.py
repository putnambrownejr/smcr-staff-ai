from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from app.schemas.source_state import SourceStateAcceptRequest, VerifiedSourceState
from app.schemas.source_updates import DocumentationUpdateCandidate, DocumentationUpdateStatusUpdate, UpdateReviewStatus
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.ingestion.source_state_store import SourceStateStore


class SourceStateService:
    def __init__(self, update_store: DocumentUpdateStore, state_store: SourceStateStore) -> None:
        self.update_store = update_store
        self.state_store = state_store

    def accept_candidate(
        self,
        candidate_id: str,
        request: SourceStateAcceptRequest,
    ) -> VerifiedSourceState | None:
        candidate = self.update_store.get(candidate_id)
        if candidate is None:
            return None

        state = VerifiedSourceState(
            source_state_id=_state_id(candidate),
            tracked_source_id=candidate.tracked_source_id,
            tracked_title=candidate.tracked_title,
            status=request.status,
            current_version=request.current_version or candidate.new_version or candidate.old_version,
            current_source_hash=request.current_source_hash or candidate.new_source_hash or candidate.old_source_hash,
            verification_source_url=request.verification_source_url or candidate.trigger_url,
            accepted_candidate_id=candidate.candidate_id,
            last_verified_at=datetime.now(UTC),
            notes=request.notes or candidate.review_notes,
        )
        self.state_store.save(state)
        self.update_store.update_status(
            candidate_id,
            DocumentationUpdateStatusUpdate(
                review_status=UpdateReviewStatus.accepted,
                review_notes=request.notes or candidate.review_notes or "Accepted into verified source state.",
            ),
        )
        return state


def _state_id(candidate: DocumentationUpdateCandidate) -> str:
    seed = candidate.tracked_source_id or candidate.tracked_title
    return hashlib.sha256(seed.encode()).hexdigest()[:20]
