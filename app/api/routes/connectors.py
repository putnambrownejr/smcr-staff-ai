from fastapi import APIRouter

from app.core.auth import LocalApiKeyDependency
from app.schemas.connectors import ConnectorConsent, ConnectorConsentResponse, ConnectorWriteAction

router = APIRouter(prefix="/connectors", tags=["connectors"], dependencies=[LocalApiKeyDependency])


@router.post("/consent-plan", response_model=ConnectorConsentResponse)
def create_consent_plan(consent: ConnectorConsent) -> ConnectorConsentResponse:
    warnings = [
        "This is a consent plan only; OAuth/token storage is not implemented.",
        "Read/write or full-access modes must still use review-before-write for generated actions.",
        "Do not store credentials, refresh tokens, CAC secrets, or mailbox/calendar content in the repo.",
    ]
    if consent.access_mode == "full_access":
        warnings.append("Full access is high risk; prefer read_write_review unless a clear use case requires it.")
    consent.warnings = [*consent.warnings, *warnings]
    return ConnectorConsentResponse(
        consent=consent,
        message="Connector consent plan created. No live external access was performed.",
    )


@router.post("/write-actions/stage", response_model=ConnectorWriteAction)
def stage_write_action(action: ConnectorWriteAction) -> ConnectorWriteAction:
    action.warnings = [
        *action.warnings,
        "Write action is staged only. No email or calendar change was performed.",
        "A future connector must require explicit user confirmation before executing this action.",
    ]
    return action
