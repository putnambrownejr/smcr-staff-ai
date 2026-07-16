from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.connector_digest import TravelEmailCaseSummary
from app.schemas.context import LocalContextMetadata
from app.schemas.travel_cases import (
    GtccCheckRecord,
    GtccCheckRequest,
    TravelCaseCreateRequest,
    TravelCaseOrganizeRequest,
    TravelCaseRecord,
    TravelLedgerEntry,
    TravelLedgerEntryRequest,
)
from app.services.connectors.travel_email_interpreter import (
    build_attachment_follow_up_prompts,
    infer_attachment_receipt_categories,
)
from app.services.session.handoff_store import is_valid_user_key


class TravelCaseStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def list_cases(self, user_key: str) -> list[TravelCaseRecord]:
        if not is_valid_user_key(user_key):
            return []
        prefix = f"{_user_digest(user_key)}-"
        items = [
            TravelCaseRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob(f"{prefix}*.json"))
        ]
        return sorted(
            items,
            key=lambda item: item.last_message_at or item.updated_at,
            reverse=True,
        )

    def upsert_many(self, user_key: str, cases: list[TravelEmailCaseSummary]) -> list[TravelCaseRecord]:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        records = self.list_cases(user_key)
        saved: list[TravelCaseRecord] = []
        for case in cases:
            merged = self._merge_one(user_key, records, case)
            records = [item for item in records if item.trip_id != merged.trip_id] + [merged]
            saved.append(merged)
        return saved

    def create_case(self, request: TravelCaseCreateRequest) -> TravelCaseRecord:
        if not is_valid_user_key(request.user_key):
            raise ValueError("Invalid user_key.")
        now = datetime.now(UTC)
        record = TravelCaseRecord(
            trip_id=secrets.token_hex(10),
            user_key=request.user_key,
            title=request.title.strip(),
            purpose=request.purpose.strip(),
            destination=request.destination.strip(),
            travel_status=request.travel_status.strip() or "watch",
            travel_start=request.travel_start,
            travel_end=request.travel_end,
            dts_authorization_ref=request.dts_authorization_ref.strip(),
            dts_voucher_ref=request.dts_voucher_ref.strip(),
            folder=request.folder.strip(),
            tags=_dedupe(request.tags),
            created_at=now,
            updated_at=now,
        )
        self._write(record)
        return record

    def set_organization(
        self,
        *,
        user_key: str,
        trip_id: str,
        request: TravelCaseOrganizeRequest,
    ) -> TravelCaseRecord:
        """Assign the trip to a folder and replace its tag set."""
        record = self._require_case(user_key, trip_id)
        updated = record.model_copy(
            update={
                "folder": request.folder.strip(),
                "tags": _dedupe(request.tags),
                "updated_at": datetime.now(UTC),
            }
        )
        self._write(updated)
        return updated

    def folders(self, user_key: str) -> list[str]:
        """Distinct, case-insensitively de-duplicated folder names, sorted."""
        return sorted(
            _dedupe([record.folder for record in self.list_cases(user_key) if record.folder]),
            key=str.casefold,
        )

    def add_ledger_entry(
        self,
        *,
        user_key: str,
        trip_id: str,
        request: TravelLedgerEntryRequest,
    ) -> TravelCaseRecord:
        record = self._require_case(user_key, trip_id)
        now = datetime.now(UTC)
        entry = TravelLedgerEntry(
            entry_id=secrets.token_hex(8),
            transaction_date=request.transaction_date,
            description=request.description.strip(),
            amount=request.amount,
            category=request.category.strip() or "other",
            payment_responsibility=request.payment_responsibility,
            notes=request.notes.strip(),
            receipt_context_id=request.receipt_context_id,
            created_at=now,
        )
        updated = record.model_copy(update={"ledger_entries": [*record.ledger_entries, entry], "updated_at": now})
        self._write(updated)
        return updated

    def remove_ledger_entry(self, *, user_key: str, trip_id: str, entry_id: str) -> TravelCaseRecord:
        record = self._require_case(user_key, trip_id)
        entries = [item for item in record.ledger_entries if item.entry_id != entry_id]
        if len(entries) == len(record.ledger_entries):
            raise ValueError(f"Unknown travel ledger entry: {entry_id}")
        updated = record.model_copy(update={"ledger_entries": entries, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def try_remove_ledger_entry(self, user_key: str, trip_id: str, entry_id: str) -> bool:
        try:
            self.remove_ledger_entry(user_key=user_key, trip_id=trip_id, entry_id=entry_id)
        except ValueError:
            return False
        return True

    def record_gtcc_check(
        self,
        *,
        user_key: str,
        trip_id: str,
        request: GtccCheckRequest,
    ) -> TravelCaseRecord:
        record = self._require_case(user_key, trip_id)
        now = datetime.now(UTC)
        check = GtccCheckRecord(
            check_id=secrets.token_hex(8),
            checked_at=request.checked_at or now,
            statement_balance=request.statement_balance,
            payment_amount=request.payment_amount,
            paid_in_full=request.paid_in_full,
            notes=request.notes.strip(),
        )
        updated = record.model_copy(update={"gtcc_checks": [*record.gtcc_checks, check], "updated_at": now})
        self._write(updated)
        return updated

    def remove_gtcc_check(self, user_key: str, trip_id: str, check_id: str) -> bool:
        try:
            record = self._require_case(user_key, trip_id)
        except ValueError:
            return False
        checks = [item for item in record.gtcc_checks if item.check_id != check_id]
        if len(checks) == len(record.gtcc_checks):
            return False
        self._write(record.model_copy(update={"gtcc_checks": checks, "updated_at": datetime.now(UTC)}))
        return True

    def delete_case(self, user_key: str, trip_id: str) -> bool:
        if not is_valid_user_key(user_key):
            return False
        path = self._path(trip_id, user_key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _merge_one(
        self,
        user_key: str,
        existing_records: list[TravelCaseRecord],
        case: TravelEmailCaseSummary,
    ) -> TravelCaseRecord:
        trip_id = _trip_id(user_key, case)
        existing = next((item for item in existing_records if item.trip_id == trip_id), None)
        now = datetime.now(UTC)
        if existing is None:
            record = TravelCaseRecord(
                trip_id=trip_id,
                user_key=user_key,
                title=case.title,
                travel_status=case.travel_status,
                travel_start=case.travel_start,
                travel_end=case.travel_end,
                voucher_due_date=case.voucher_due_date,
                rental_car_expected=case.rental_car_expected,
                receipts_to_collect=_dedupe(case.receipts_to_collect),
                attached_receipt_categories=_dedupe(case.attached_receipt_categories),
                attachment_names=_dedupe(case.attachment_names),
                attachment_follow_up_prompts=_dedupe(case.attachment_follow_up_prompts),
                linked_receipt_context_ids=[],
                source_subjects=_dedupe([case.source_subject]),
                source_senders=_dedupe([case.sender] if case.sender else []),
                last_message_at=case.message_received_at,
                created_at=now,
                updated_at=now,
                confidence_notes=_dedupe(case.confidence_notes),
                recommendations=_dedupe(case.recommendations),
            )
        else:
            record = existing.model_copy(
                update={
                    "title": _prefer_title(existing.title, case.title),
                    "travel_status": _merge_status(existing.travel_status, case.travel_status),
                    "travel_start": case.travel_start or existing.travel_start,
                    "travel_end": case.travel_end or existing.travel_end,
                    "voucher_due_date": case.voucher_due_date or existing.voucher_due_date,
                    "rental_car_expected": existing.rental_car_expected or case.rental_car_expected,
                    "receipts_to_collect": _dedupe([*existing.receipts_to_collect, *case.receipts_to_collect]),
                    "attached_receipt_categories": _dedupe(
                        [*existing.attached_receipt_categories, *case.attached_receipt_categories]
                    ),
                    "attachment_names": _dedupe([*existing.attachment_names, *case.attachment_names]),
                    "attachment_follow_up_prompts": _dedupe(
                        [*existing.attachment_follow_up_prompts, *case.attachment_follow_up_prompts]
                    ),
                    "source_subjects": _dedupe([*existing.source_subjects, case.source_subject]),
                    "source_senders": _dedupe([*existing.source_senders, *([case.sender] if case.sender else [])]),
                    "last_message_at": _latest(existing.last_message_at, case.message_received_at),
                    "updated_at": now,
                    "confidence_notes": _dedupe([*existing.confidence_notes, *case.confidence_notes]),
                    "recommendations": _dedupe([*existing.recommendations, *case.recommendations]),
                }
            )
        self._write(record)
        return record

    def get_case(self, user_key: str, trip_id: str) -> TravelCaseRecord | None:
        if not is_valid_user_key(user_key):
            return None
        path = self._path(trip_id, user_key)
        if not path.exists():
            return None
        return TravelCaseRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def link_receipt(
        self,
        *,
        user_key: str,
        trip_id: str,
        context: LocalContextMetadata,
        receipt_category: str | None = None,
    ) -> TravelCaseRecord:
        record = self.get_case(user_key, trip_id)
        if record is None:
            raise ValueError(f"Unknown travel case: {trip_id}")
        inferred_categories = (
            [receipt_category.strip()]
            if receipt_category and receipt_category.strip()
            else infer_attachment_receipt_categories([context.filename])
        )
        attached_receipt_categories = _dedupe([*record.attached_receipt_categories, *inferred_categories])
        attachment_names = _dedupe([*record.attachment_names, context.filename])
        linked_context_ids = _dedupe([*record.linked_receipt_context_ids, context.context_id])
        follow_up_prompts = build_attachment_follow_up_prompts(
            receipts_to_collect=record.receipts_to_collect,
            attached_receipt_categories=attached_receipt_categories,
            attachment_names=attachment_names,
            title=record.title,
        )
        updated_payload = record.model_dump()
        updated_payload.update(
            attached_receipt_categories=attached_receipt_categories,
            attachment_names=attachment_names,
            linked_receipt_context_ids=linked_context_ids,
            attachment_follow_up_prompts=_dedupe(follow_up_prompts),
            updated_at=datetime.now(UTC),
        )
        updated = TravelCaseRecord(**updated_payload)
        self._write(updated)
        return updated

    def _require_case(self, user_key: str, trip_id: str) -> TravelCaseRecord:
        record = self.get_case(user_key, trip_id)
        if record is None:
            raise ValueError(f"Unknown travel case: {trip_id}")
        return record

    def _write(self, record: TravelCaseRecord) -> None:
        self._path(record.trip_id, record.user_key).write_text(
            record.model_dump_json(indent=2, exclude_computed_fields=True),
            encoding="utf-8",
        )

    def _path(self, trip_id: str, user_key: str) -> Path:
        return self.root_dir / f"{_user_digest(user_key)}-{trip_id}.json"


def _trip_id(user_key: str, case: TravelEmailCaseSummary) -> str:
    date_seed = "::".join(
        part
        for part in [
            case.travel_start.isoformat() if case.travel_start else "",
            case.travel_end.isoformat() if case.travel_end else "",
        ]
        if part
    )
    title_seed = _normalize_title(case.title)
    raw = "::".join(
        [
            user_key,
            date_seed or title_seed,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _user_digest(user_key: str) -> str:
    return hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]


def _normalize_title(title: str) -> str:
    lowered = title.lower()
    for token in ["ci travel", "dts", "voucher", "itinerary", "rental car", "confirmation", "reminder"]:
        lowered = lowered.replace(token, " ")
    normalized = " ".join(lowered.split())
    return normalized or "travel"


def _merge_status(existing: str, new: str) -> str:
    rank = {"watch": 0, "upcoming_travel": 1, "post_travel": 2}
    return existing if rank.get(existing, 0) >= rank.get(new, 0) else new


def _prefer_title(existing: str, new: str) -> str:
    if len(new) > len(existing) and "travel" in new.lower():
        return new
    return existing


def _latest(existing: datetime | None, new: datetime | None) -> datetime | None:
    if existing is None:
        return new
    if new is None:
        return existing
    return max(existing, new)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result
