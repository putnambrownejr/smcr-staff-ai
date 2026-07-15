from __future__ import annotations

from datetime import date
from pathlib import Path

from app.schemas.cadences import CadenceCreateRequest
from app.schemas.chief_capabilities import (
    ChiefCapabilityOperation,
    ChiefCapabilityRequest,
    ChiefCapabilityResponse,
    ChiefDomainSummary,
    ChiefUndoResponse,
)
from app.schemas.fitreps import (
    FitrepImprovementGoalRequest,
    FitrepReportCreateRequest,
    RsProfileSnapshotCreateRequest,
)
from app.schemas.travel_cases import GtccCheckRequest, TravelLedgerEntryRequest
from app.services.chief.capability_audit_store import CapabilityAuditStore
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.fitness.cadence_store import CadenceStore
from app.services.fitreps.store import FitrepStore

_READABLE_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".js", ".html", ".css", ".toml"}
_EXCLUDED_PARTS = {".git", ".venv", "node_modules", "projects", "__pycache__", ".pytest_cache", ".mypy_cache"}


class ChiefCapabilityGateway:
    def __init__(
        self,
        *,
        travel_store: TravelCaseStore,
        fitrep_store: FitrepStore,
        cadence_store: CadenceStore,
        audit_store: CapabilityAuditStore,
        repository_root: str | Path,
    ) -> None:
        self.travel_store = travel_store
        self.fitrep_store = fitrep_store
        self.cadence_store = cadence_store
        self.audit_store = audit_store
        self.repository_root = Path(repository_root).resolve()

    def summary(self, user_key: str) -> ChiefDomainSummary:
        travel = self.travel_store.list_cases(user_key)
        fitrep = self.fitrep_store.get(user_key)
        private_cadences = [
            item for item in self.cadence_store.list_records(user_key, include_adult=True) if not item.built_in
        ]
        return ChiefDomainSummary(
            user_key=user_key,
            travel_case_count=len(travel),
            travel_ledger_entry_count=sum(len(item.ledger_entries) for item in travel),
            gtcc_check_count=sum(len(item.gtcc_checks) for item in travel),
            fitrep_report_count=len(fitrep.reports),
            rs_profile_snapshot_count=len(fitrep.rs_profiles),
            fitrep_goal_count=len(fitrep.goals),
            private_cadence_count=len(private_cadences),
        )

    def execute(self, request: ChiefCapabilityRequest) -> ChiefCapabilityResponse:
        operation = request.operation
        if operation is ChiefCapabilityOperation.read_summary:
            return ChiefCapabilityResponse(
                operation=operation, result=self.summary(request.user_key).model_dump(mode="json")
            )
        if operation is ChiefCapabilityOperation.search_repository:
            query = str(request.payload.get("query", "")).strip()
            path = str(request.payload.get("path", "")).strip() or None
            return ChiefCapabilityResponse(operation=operation, result=self.search_repository(query, path=path))

        target_id, parent_id, result = self._append(request)
        audit = self.audit_store.create(
            user_key=request.user_key,
            operation=operation.value,
            undo_kind=operation.value,
            target_id=target_id,
            parent_id=parent_id,
        )
        return ChiefCapabilityResponse(
            operation=operation,
            result=result,
            changed=True,
            undo_token=audit.undo_token,
            warnings=["This was an explicit append. Use Undo to remove only the record created by this operation."],
        )

    def undo(self, user_key: str, undo_token: str) -> ChiefUndoResponse:
        audit = self.audit_store.get_active(user_key, undo_token)
        if audit is None:
            raise ValueError("Unknown, expired, or already-used undo token.")
        kind = ChiefCapabilityOperation(audit.undo_kind)
        undone = self._undo_record(kind, user_key, audit.target_id, audit.parent_id)
        if not undone:
            raise ValueError("The appended record no longer exists; no change was made.")
        self.audit_store.mark_used(user_key, undo_token)
        return ChiefUndoResponse(undo_token=undo_token, undone=True, message="The appended record was removed.")

    def search_repository(self, query: str, *, path: str | None = None) -> list[dict[str, object]]:
        if len(query.strip()) < 2:
            raise ValueError("Repository search query must contain at least two characters.")
        start = self._resolve_read_path(path)
        candidates = [start] if start.is_file() else start.rglob("*")
        needle = query.casefold()
        matches: list[dict[str, object]] = []
        for candidate in candidates:
            if len(matches) >= 50:
                break
            if not candidate.is_file() or candidate.suffix.lower() not in _READABLE_SUFFIXES:
                continue
            relative = candidate.relative_to(self.repository_root)
            if any(part in _EXCLUDED_PARTS for part in relative.parts):
                continue
            if candidate.stat().st_size > 1_000_000:
                continue
            try:
                lines = candidate.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if needle in line.casefold() or needle in relative.as_posix().casefold():
                    matches.append({"path": relative.as_posix(), "line": line_number, "text": line.strip()[:240]})
                    break
        return matches

    def _resolve_read_path(self, path: str | None) -> Path:
        candidate = (self.repository_root / (path or ".")).resolve()
        if candidate != self.repository_root and self.repository_root not in candidate.parents:
            raise ValueError("Repository path must remain inside the repository root.")
        relative = candidate.relative_to(self.repository_root)
        if any(part in _EXCLUDED_PARTS for part in relative.parts):
            raise ValueError("Repository path is excluded from Chief access.")
        if not candidate.exists():
            raise ValueError("Repository path does not exist.")
        return candidate

    def _append(self, request: ChiefCapabilityRequest) -> tuple[str, str | None, dict[str, object]]:
        payload = {**request.payload, "user_key": request.user_key}
        operation = request.operation
        if operation is ChiefCapabilityOperation.append_travel_ledger:
            trip_id = self._require_trip_id(payload)
            payload.setdefault("transaction_date", date.today().isoformat())
            before = self.travel_store.get_case(request.user_key, trip_id)
            if before is None:
                raise ValueError(f"Unknown travel case: {trip_id}")
            ledger_request = TravelLedgerEntryRequest.model_validate(payload)
            after = self.travel_store.add_ledger_entry(
                user_key=request.user_key, trip_id=trip_id, request=ledger_request
            )
            ledger_entry = next(
                item
                for item in after.ledger_entries
                if item.entry_id not in {x.entry_id for x in before.ledger_entries}
            )
            return ledger_entry.entry_id, trip_id, ledger_entry.model_dump(mode="json")
        if operation is ChiefCapabilityOperation.append_gtcc_check:
            trip_id = self._require_trip_id(payload)
            before = self.travel_store.get_case(request.user_key, trip_id)
            if before is None:
                raise ValueError(f"Unknown travel case: {trip_id}")
            check_request = GtccCheckRequest.model_validate(payload)
            after = self.travel_store.record_gtcc_check(
                user_key=request.user_key, trip_id=trip_id, request=check_request
            )
            gtcc_check = next(
                item for item in after.gtcc_checks if item.check_id not in {x.check_id for x in before.gtcc_checks}
            )
            return gtcc_check.check_id, trip_id, gtcc_check.model_dump(mode="json")
        if operation is ChiefCapabilityOperation.append_fitrep_report:
            report = self.fitrep_store.add_report(FitrepReportCreateRequest.model_validate(payload))
            return report.report_id, None, report.model_dump(mode="json")
        if operation is ChiefCapabilityOperation.append_rs_profile:
            snapshot = self.fitrep_store.add_rs_snapshot(RsProfileSnapshotCreateRequest.model_validate(payload))
            return snapshot.snapshot_id, None, snapshot.model_dump(mode="json")
        if operation is ChiefCapabilityOperation.append_fitrep_goal:
            payload.pop("goal_id", None)
            goal = self.fitrep_store.upsert_goal(FitrepImprovementGoalRequest.model_validate(payload))
            return goal.goal_id, None, goal.model_dump(mode="json")
        if operation is ChiefCapabilityOperation.append_cadence:
            cadence = self.cadence_store.create(CadenceCreateRequest.model_validate(payload))
            return cadence.cadence_id, None, cadence.model_dump(mode="json")
        raise ValueError(f"Unsupported Chief capability operation: {operation.value}")

    def _undo_record(
        self,
        kind: ChiefCapabilityOperation,
        user_key: str,
        target_id: str,
        parent_id: str | None,
    ) -> bool:
        if kind is ChiefCapabilityOperation.append_travel_ledger and parent_id:
            return self.travel_store.try_remove_ledger_entry(user_key, parent_id, target_id)
        if kind is ChiefCapabilityOperation.append_gtcc_check and parent_id:
            return self.travel_store.remove_gtcc_check(user_key, parent_id, target_id)
        if kind is ChiefCapabilityOperation.append_fitrep_report:
            return self.fitrep_store.delete_report(user_key, target_id)
        if kind is ChiefCapabilityOperation.append_rs_profile:
            return self.fitrep_store.delete_rs_snapshot(user_key, target_id)
        if kind is ChiefCapabilityOperation.append_fitrep_goal:
            return self.fitrep_store.delete_goal(user_key, target_id)
        if kind is ChiefCapabilityOperation.append_cadence:
            return self.cadence_store.delete(user_key, target_id)
        return False

    @staticmethod
    def _require_trip_id(payload: dict[str, object]) -> str:
        trip_id = str(payload.pop("trip_id", "")).strip()
        if not trip_id:
            raise ValueError("trip_id is required for travel capability operations.")
        return trip_id
