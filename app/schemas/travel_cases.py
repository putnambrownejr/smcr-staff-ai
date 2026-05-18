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
    source_subjects: list[str] = Field(default_factory=list)
    source_senders: list[str] = Field(default_factory=list)
    last_message_at: datetime | None = None
    updated_at: datetime
    confidence_notes: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    local_only: bool = True

