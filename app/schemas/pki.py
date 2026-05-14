from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PkiIssueType(StrEnum):
    general = "general"
    cac_not_detected = "cac_not_detected"
    certificate_issue = "certificate_issue"
    middleware_issue = "middleware_issue"
    browser_auth_issue = "browser_auth_issue"
    signing_encryption_issue = "signing_encryption_issue"
    portal_access_issue = "portal_access_issue"
    reader_hardware_issue = "reader_hardware_issue"


class PkiTroubleshootingRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "MarineNet CAC login issue",
                "issue_type": "browser_auth_issue",
                "symptoms": ["CAC is recognized but certificate prompt never appears."],
                "environment_notes": ["Occurs on home Wi-Fi", "Chrome works inconsistently"],
                "affected_systems": ["MarineNet", "microsoft365.us"],
                "browser": "Chrome",
                "using_vpn": False,
                "on_government_furnished_equipment": False,
            }
        }
    )

    title: str
    issue_type: PkiIssueType = PkiIssueType.general
    symptoms: list[str] = Field(default_factory=list)
    environment_notes: list[str] = Field(default_factory=list)
    affected_systems: list[str] = Field(default_factory=list)
    browser: str | None = None
    using_vpn: bool | None = None
    on_government_furnished_equipment: bool | None = None


class PkiTroubleshootingResponse(BaseModel):
    title: str
    issue_type: PkiIssueType
    summary_lines: list[str] = Field(default_factory=list)
    likely_causes: list[str] = Field(default_factory=list)
    immediate_checks: list[str] = Field(default_factory=list)
    deeper_checks: list[str] = Field(default_factory=list)
    escalation_path: list[str] = Field(default_factory=list)
    safe_data_handling_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
