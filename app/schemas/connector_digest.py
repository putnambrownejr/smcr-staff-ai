from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chief import ChiefActionItem
from app.schemas.connectors import ConnectorConsent, ConnectorProvider, ConnectorWriteAction


class ConnectorEventSummary(BaseModel):
    provider: ConnectorProvider
    title: str
    start_at: datetime
    end_at: datetime | None = None
    location: str | None = None
    category: str = "calendar"
    notes: str | None = None


class ConnectorMessageSummary(BaseModel):
    provider: ConnectorProvider
    subject: str
    sender: str | None = None
    received_at: datetime
    category: str = "email"
    action_hint: str | None = None
    notes: str | None = None


class ChiefConnectorDigestRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_key": "capt-example",
                "consents": [
                    {
                        "provider": "google_calendar",
                        "access_mode": "read_only",
                        "user_key": "capt-example",
                        "enabled": False,
                    }
                ],
                "calendar_events": [
                    {
                        "provider": "google_calendar",
                        "title": "Drill weekend muster",
                        "start_at": "2026-06-06T08:00:00Z",
                        "location": "NOSC New Orleans",
                    }
                ],
                "email_messages": [
                    {
                        "provider": "gmail",
                        "subject": "DTS voucher reminder",
                        "received_at": "2026-06-07T14:30:00Z",
                        "action_hint": "Voucher due this week",
                    }
                ],
            }
        }
    )
    user_key: str
    consents: list[ConnectorConsent] = Field(default_factory=list)
    calendar_events: list[ConnectorEventSummary] = Field(default_factory=list)
    email_messages: list[ConnectorMessageSummary] = Field(default_factory=list)


class ConnectorReadPlan(BaseModel):
    provider: ConnectorProvider
    enabled: bool
    access_mode: str
    what_would_be_read: list[str] = Field(default_factory=list)
    safeguards: list[str] = Field(default_factory=list)


class ChiefConnectorDigestResponse(BaseModel):
    title: str
    user_key: str
    summary_lines: list[str] = Field(default_factory=list)
    read_plans: list[ConnectorReadPlan] = Field(default_factory=list)
    action_items: list[ChiefActionItem] = Field(default_factory=list)
    staged_write_actions: list[ConnectorWriteAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
