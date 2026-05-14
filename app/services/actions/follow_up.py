from __future__ import annotations

from app.schemas.actions import ActionFollowUpRequest, ActionStatus, ActionUpdateRequest
from app.services.actions.tracker import ActionTracker


class ActionFollowUpProcessor:
    def apply(
        self,
        tracker: ActionTracker,
        request: ActionFollowUpRequest,
    ) -> list[tuple[str, str, ActionStatus, str | None]]:
        results: list[tuple[str, str, ActionStatus, str | None]] = []
        status = request.status or _infer_status(request.notes)
        for action_id in request.action_ids:
            record = tracker.get(action_id)
            if record is None:
                continue
            merged_notes = _merge_notes(record.notes, request.notes)
            updated = tracker.update(
                action_id,
                ActionUpdateRequest(
                    status=status,
                    notes=merged_notes,
                ),
            )
            if updated is not None:
                results.append((updated.action_id, updated.title, updated.status, updated.notes))
        return results


def _infer_status(notes: str) -> ActionStatus:
    lowered = notes.lower()
    if any(token in lowered for token in ("complete", "completed", "done", "closed", "finished")):
        return ActionStatus.complete
    if any(token in lowered for token in ("blocked", "waiting", "awaiting", "pending external")):
        return ActionStatus.waiting if "waiting" in lowered or "awaiting" in lowered else ActionStatus.blocked
    if any(token in lowered for token in ("started", "working", "in progress", "drafted", "reviewed")):
        return ActionStatus.in_progress
    return ActionStatus.open


def _merge_notes(existing: str | None, new_notes: str) -> str:
    if not existing:
        return f"Follow-up: {new_notes}"
    return f"{existing}\nFollow-up: {new_notes}"
