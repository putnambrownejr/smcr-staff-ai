"""Approved external LLM client for scenario-mode assessment population."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

import httpx

from app.schemas.external_processing import (
    DisclosureMode,
    ExternalProcessingApproval,
    ExternalProcessingAuditEntry,
    ExternalProcessingOutcome,
    ExternalProcessingPreview,
)
from app.services.external_processing.audit_store import ExternalProcessingAuditStore
from app.services.external_processing.preflight import (
    ExternalProcessingApprovalRequiredError,
    ExternalProcessingPreflightService,
    ExternalProcessingPreviewReadyError,
)

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0
_NO_KEY_WARNED = False


class ScenarioGenerationStatus(StrEnum):
    generated = "generated"
    local_only = "local_only"
    unavailable = "unavailable"
    failed = "failed"


@dataclass(frozen=True)
class ScenarioGenerationResult:
    content: str | None
    status: ScenarioGenerationStatus
    preview: ExternalProcessingPreview
    disclosure_mode: DisclosureMode | None = None
    warning_override_authorized: bool = False


@lru_cache
def _llm_settings() -> tuple[str | None, str, str]:
    from app.core.config import get_settings

    settings = get_settings()
    return settings.llm_api_key, settings.llm_base_url, settings.llm_model


def generate_scenario_response(
    system_prompt: str,
    template: str,
    user_input: str,
    *,
    approval: ExternalProcessingApproval | None = None,
    preview_only: bool = False,
    user_key: str | None = None,
    scope_label: str = "agent:scenario",
    expected_call_count: int = 1,
    approval_digest_override: str | None = None,
) -> ScenarioGenerationResult:
    """Generate a scenario response only from a preflight-approved payload."""
    global _NO_KEY_WARNED  # noqa: PLW0603
    api_key, base_url, model = _llm_settings()
    service = ExternalProcessingPreflightService()
    preview = service.build_preview(
        system_prompt=system_prompt,
        template=template,
        user_input=user_input,
        base_url=base_url,
        model=model,
        scope_label=scope_label,
        external_available=bool(api_key),
        expected_call_count=expected_call_count,
        approval_digest_override=approval_digest_override,
    )

    if preview_only:
        raise ExternalProcessingPreviewReadyError(preview)

    try:
        payload = service.authorize(preview, approval)
    except ExternalProcessingApprovalRequiredError as exc:
        if "stale" in exc.reason.lower():
            _record_audit(
                user_key=user_key,
                preview=preview,
                approval=approval,
                outcome=ExternalProcessingOutcome.stale,
                completed_call_count=0,
            )
        raise

    if payload is None:
        if api_key and approval is not None and approval.disclosure_mode is DisclosureMode.local_only:
            _record_audit(
                user_key=user_key,
                preview=preview,
                approval=approval,
                outcome=ExternalProcessingOutcome.local_only,
                completed_call_count=0,
            )
            return ScenarioGenerationResult(
                content=None,
                status=ScenarioGenerationStatus.local_only,
                preview=preview,
                disclosure_mode=DisclosureMode.local_only,
            )
        if not api_key and not _NO_KEY_WARNED:
            logger.warning(
                "LLM_API_KEY not set — scenario field population disabled. "
                "Scenario assessments will use local deterministic templates."
            )
            _NO_KEY_WARNED = True
        return ScenarioGenerationResult(
            content=None,
            status=ScenarioGenerationStatus.unavailable,
            preview=preview,
        )

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [message.model_dump() for message in payload.messages],
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            content = _response_content(response.json())
            if content:
                _record_audit(
                    user_key=user_key,
                    preview=preview,
                    approval=approval,
                    outcome=ExternalProcessingOutcome.completed,
                    completed_call_count=1,
                )
                return ScenarioGenerationResult(
                    content=content,
                    status=ScenarioGenerationStatus.generated,
                    preview=preview,
                    disclosure_mode=payload.disclosure_mode,
                    warning_override_authorized=True,
                )
    except Exception:
        logger.warning("Approved LLM scenario call failed; falling back to template", exc_info=True)

    _record_audit(
        user_key=user_key,
        preview=preview,
        approval=approval,
        outcome=ExternalProcessingOutcome.failed,
        completed_call_count=0,
    )
    return ScenarioGenerationResult(
        content=None,
        status=ScenarioGenerationStatus.failed,
        preview=preview,
        disclosure_mode=payload.disclosure_mode,
        warning_override_authorized=True,
    )


def _response_content(data: object) -> str | None:
    if not isinstance(data, dict):
        return None
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        return None
    return content.strip()


def _record_audit(
    *,
    user_key: str | None,
    preview: ExternalProcessingPreview,
    approval: ExternalProcessingApproval | None,
    outcome: ExternalProcessingOutcome,
    completed_call_count: int,
) -> None:
    from app.core.config import get_settings

    settings = get_settings()
    store = ExternalProcessingAuditStore(settings.external_processing_audits_storage_dir)
    disclosure_mode = approval.disclosure_mode if approval is not None else DisclosureMode.local_only
    store.append(
        user_key,
        ExternalProcessingAuditEntry(
            scope_label=preview.scope_label,
            user_key_digest="replaced-by-store",
            provider=preview.provider,
            model=preview.model,
            disclosure_mode=disclosure_mode,
            finding_categories=preview.finding_categories,
            approval_digest=preview.approval_digest,
            payload_digest=preview.payload_digest,
            expected_call_count=preview.expected_call_count,
            completed_call_count=completed_call_count,
            outcome=outcome,
        ),
    )
