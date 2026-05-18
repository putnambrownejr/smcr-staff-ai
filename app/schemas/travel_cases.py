from datetime import date, datetime

from pydantic import BaseModel, Field


class TravelCaseRecord(BaseModel):
    trip_id: str
    user_key: str
    title: str
    travel_status: str = "watch"
    travel_start: date | None = None
    travel_end: date | None = None
    voucher_due_date: date | None = None
    rental_car_expected: bool = False
    receipts_to_collect: list[str] = Field(default_factory=list)
    attached_receipt_categories: list[str] = Field(default_factory=list)
    attachment_names: list[str] = Field(default_factory=list)
    attachment_follow_up_prompts: list[str] = Field(default_factory=list)
    linked_receipt_context_ids: list[str] = Field(default_factory=list)
    source_subjects: list[str] = Field(default_factory=list)
    source_senders: list[str] = Field(default_factory=list)
    last_message_at: datetime | None = None
    updated_at: datetime
    confidence_notes: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    local_only: bool = True


class LinkTravelReceiptRequest(BaseModel):
    user_key: str
    context_id: str
    receipt_category: str | None = None


class TravelCaseListResponse(BaseModel):
    total_cases: int
    records: list[TravelCaseRecord] = Field(default_factory=list)
