from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class TravelLedgerEntry(BaseModel):
    entry_id: str
    transaction_date: date
    description: str
    amount: Decimal
    category: str = "other"
    payment_responsibility: Literal["gtcc", "personal", "reimbursed", "unknown"] = "gtcc"
    notes: str = ""
    receipt_context_id: str | None = None
    source: Literal["user_entered"] = "user_entered"
    created_at: datetime


class GtccCheckRecord(BaseModel):
    check_id: str
    checked_at: datetime
    statement_balance: Decimal | None = Field(default=None, ge=0)
    payment_amount: Decimal | None = Field(default=None, ge=0)
    paid_in_full: bool = False
    notes: str = ""
    source: Literal["user_entered"] = "user_entered"


class TravelCaseCreateRequest(BaseModel):
    user_key: str
    title: str = Field(min_length=1, max_length=200)
    purpose: str = ""
    destination: str = ""
    travel_start: date | None = None
    travel_end: date | None = None
    travel_status: str = "watch"
    dts_authorization_ref: str = ""
    dts_voucher_ref: str = ""
    folder: str = Field(default="", max_length=120)
    tags: list[str] = Field(default_factory=list)


class TravelCaseOrganizeRequest(BaseModel):
    """Set a trip's folder and/or tags without touching the rest of the record."""

    user_key: str
    folder: str = Field(default="", max_length=120)
    tags: list[str] = Field(default_factory=list)


class TravelLedgerEntryRequest(BaseModel):
    user_key: str
    transaction_date: date
    description: str = Field(min_length=1, max_length=200)
    amount: Decimal
    category: str = "other"
    payment_responsibility: Literal["gtcc", "personal", "reimbursed", "unknown"] = "gtcc"
    notes: str = ""
    receipt_context_id: str | None = None


class GtccCheckRequest(BaseModel):
    user_key: str
    checked_at: datetime | None = None
    statement_balance: Decimal | None = Field(default=None, ge=0)
    payment_amount: Decimal | None = Field(default=None, ge=0)
    paid_in_full: bool = False
    notes: str = ""


class TravelCaseRecord(BaseModel):
    trip_id: str
    user_key: str
    title: str
    purpose: str = ""
    destination: str = ""
    folder: str = ""
    tags: list[str] = Field(default_factory=list)
    travel_status: str = "watch"
    travel_start: date | None = None
    travel_end: date | None = None
    voucher_due_date: date | None = None
    dts_authorization_ref: str = ""
    dts_voucher_ref: str = ""
    rental_car_expected: bool = False
    receipts_to_collect: list[str] = Field(default_factory=list)
    attached_receipt_categories: list[str] = Field(default_factory=list)
    attachment_names: list[str] = Field(default_factory=list)
    attachment_follow_up_prompts: list[str] = Field(default_factory=list)
    linked_receipt_context_ids: list[str] = Field(default_factory=list)
    source_subjects: list[str] = Field(default_factory=list)
    source_senders: list[str] = Field(default_factory=list)
    ledger_entries: list[TravelLedgerEntry] = Field(default_factory=list)
    gtcc_checks: list[GtccCheckRecord] = Field(default_factory=list)
    last_message_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime
    confidence_notes: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    local_only: bool = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def estimated_spend_total(self) -> Decimal:
        return sum((entry.amount for entry in self.ledger_entries), Decimal("0.00"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def latest_gtcc_check(self) -> GtccCheckRecord | None:
        if not self.gtcc_checks:
            return None
        return max(self.gtcc_checks, key=lambda item: item.checked_at)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def data_source(self) -> str:
        if self.source_subjects and not self.ledger_entries and not self.gtcc_checks:
            return "connector"
        return "user_entered_or_connector"


class LinkTravelReceiptRequest(BaseModel):
    user_key: str
    context_id: str
    receipt_category: str | None = None


class TravelCaseListResponse(BaseModel):
    total_cases: int
    records: list[TravelCaseRecord] = Field(default_factory=list)
    folders: list[str] = Field(default_factory=list)
