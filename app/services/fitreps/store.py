from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.fitreps import (
    FitrepImprovementGoal,
    FitrepImprovementGoalRequest,
    FitrepReport,
    FitrepReportCreateRequest,
    FitrepWorkspace,
    RsProfileSnapshot,
    RsProfileSnapshotCreateRequest,
)
from app.services.session.handoff_store import is_valid_user_key


class FitrepStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_key: str) -> FitrepWorkspace:
        if not is_valid_user_key(user_key):
            return FitrepWorkspace(user_key=user_key)
        path = self._path(user_key)
        if not path.exists():
            return FitrepWorkspace(user_key=user_key)
        return FitrepWorkspace.model_validate_json(path.read_text(encoding="utf-8"))

    def add_report(self, request: FitrepReportCreateRequest) -> FitrepReport:
        workspace = self._require_workspace(request.user_key)
        now = datetime.now(UTC)
        report = FitrepReport(**request.model_dump(), report_id=secrets.token_hex(8), created_at=now, updated_at=now)
        self._write(workspace.model_copy(update={"reports": [*workspace.reports, report], "updated_at": now}))
        return report

    def update_report(
        self,
        user_key: str,
        report_id: str,
        request: FitrepReportCreateRequest,
    ) -> FitrepReport:
        if request.user_key != user_key:
            raise ValueError("user_key mismatch.")
        workspace = self._require_workspace(user_key)
        existing = next((item for item in workspace.reports if item.report_id == report_id), None)
        if existing is None:
            raise ValueError(f"Unknown FitRep report: {report_id}")
        updated = FitrepReport(
            **request.model_dump(),
            report_id=report_id,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
        )
        self._write(
            workspace.model_copy(
                update={
                    "reports": [updated if item.report_id == report_id else item for item in workspace.reports],
                    "updated_at": updated.updated_at,
                }
            )
        )
        return updated

    def delete_report(self, user_key: str, report_id: str) -> bool:
        workspace = self.get(user_key)
        reports = [item for item in workspace.reports if item.report_id != report_id]
        if len(reports) == len(workspace.reports):
            return False
        self._write(workspace.model_copy(update={"reports": reports, "updated_at": datetime.now(UTC)}))
        return True

    def add_rs_snapshot(self, request: RsProfileSnapshotCreateRequest) -> RsProfileSnapshot:
        workspace = self._require_workspace(request.user_key)
        snapshot = RsProfileSnapshot(**request.model_dump(), snapshot_id=secrets.token_hex(8))
        self._write(
            workspace.model_copy(
                update={"rs_profiles": [*workspace.rs_profiles, snapshot], "updated_at": datetime.now(UTC)}
            )
        )
        return snapshot

    def delete_rs_snapshot(self, user_key: str, snapshot_id: str) -> bool:
        workspace = self.get(user_key)
        snapshots = [item for item in workspace.rs_profiles if item.snapshot_id != snapshot_id]
        if len(snapshots) == len(workspace.rs_profiles):
            return False
        self._write(workspace.model_copy(update={"rs_profiles": snapshots, "updated_at": datetime.now(UTC)}))
        return True

    def upsert_goal(self, request: FitrepImprovementGoalRequest) -> FitrepImprovementGoal:
        workspace = self._require_workspace(request.user_key)
        now = datetime.now(UTC)
        goal_id = request.goal_id or secrets.token_hex(8)
        existing = next((item for item in workspace.goals if item.goal_id == goal_id), None)
        goal = FitrepImprovementGoal(
            **request.model_dump(exclude={"goal_id"}),
            goal_id=goal_id,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        goals = [goal if item.goal_id == goal_id else item for item in workspace.goals]
        if existing is None:
            goals.append(goal)
        self._write(workspace.model_copy(update={"goals": goals, "updated_at": now}))
        return goal

    def delete_goal(self, user_key: str, goal_id: str) -> bool:
        workspace = self.get(user_key)
        goals = [item for item in workspace.goals if item.goal_id != goal_id]
        if len(goals) == len(workspace.goals):
            return False
        self._write(workspace.model_copy(update={"goals": goals, "updated_at": datetime.now(UTC)}))
        return True

    def _require_workspace(self, user_key: str) -> FitrepWorkspace:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        return self.get(user_key)

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"

    def _write(self, workspace: FitrepWorkspace) -> None:
        self._path(workspace.user_key).write_text(workspace.model_dump_json(indent=2), encoding="utf-8")
