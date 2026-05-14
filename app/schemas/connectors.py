from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class ConnectorProvider(StrEnum):
    google_calendar = "google_calendar"
    microsoft_graph_calendar = "microsoft_graph_calendar"
    gmail = "gmail"
    outlook_email = "outlook_email"


class ConnectorAccessMode(StrEnum):
    read_only = "read_only"
    read_write_review = "read_write_review"
    full_access = "full_access"


class ConnectorConsent(BaseModel):
    provider: ConnectorProvider
    access_mode: ConnectorAccessMode = ConnectorAccessMode.read_only
    scopes: list[str] = Field(default_factory=list)
    user_key: str
    review_before_write: bool = True
    token_storage_policy: str = "not_implemented"
    enabled: bool = False
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_consent_invariants(self) -> Self:
        write_scopes = [scope for scope in self.scopes if "write" in scope.lower() or "modify" in scope.lower()]
        if self.access_mode == ConnectorAccessMode.read_only and write_scopes:
            raise ValueError("read_only connectors cannot request write/modify scopes.")
        if self.access_mode == ConnectorAccessMode.read_write_review and not self.review_before_write:
            raise ValueError("read_write_review connectors must keep review_before_write=true.")
        if self.access_mode == ConnectorAccessMode.full_access and self.enabled:
            raise ValueError("full_access cannot be enabled by default in this prototype.")
        return self


class ConnectorWriteAction(BaseModel):
    provider: ConnectorProvider
    user_key: str
    action_type: str
    target_id: str | None = None
    payload_summary: str
    confirmation_token: str
    staged_only: bool = True
    warnings: list[str] = Field(default_factory=list)


class ConnectorConsentResponse(BaseModel):
    consent: ConnectorConsent
    message: str
