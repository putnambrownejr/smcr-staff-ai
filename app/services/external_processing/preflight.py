from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.security import external_processing_categories, redact_for_external_processing
from app.schemas.external_processing import (
    DisclosureMode,
    ExternalProcessingApproval,
    ExternalProcessingFinding,
    ExternalProcessingMessage,
    ExternalProcessingPreview,
    ExternalProcessingSeverity,
)


@dataclass(frozen=True)
class ApprovedExternalPayload:
    messages: list[ExternalProcessingMessage]
    disclosure_mode: DisclosureMode
    approval_digest: str
    finding_categories: list[str]


class ExternalProcessingApprovalRequiredError(ValueError):
    def __init__(self, preview: ExternalProcessingPreview, reason: str) -> None:
        super().__init__(reason)
        self.preview = preview
        self.reason = reason


class ExternalProcessingPreviewReadyError(RuntimeError):
    def __init__(self, preview: ExternalProcessingPreview) -> None:
        super().__init__("External processing preview is ready.")
        self.preview = preview


class ExternalProcessingPreflightService:
    def build_preview(
        self,
        *,
        system_prompt: str,
        template: str,
        user_input: str,
        base_url: str,
        model: str,
        scope_label: str,
        external_available: bool,
        expected_call_count: int = 1,
        approval_digest_override: str | None = None,
    ) -> ExternalProcessingPreview:
        if not external_available:
            return ExternalProcessingPreview(
                required=False,
                external_available=False,
                scope_label=scope_label,
                warnings=["No external LLM is configured. The local deterministic template will be used."],
            )

        original_messages = build_scenario_messages(system_prompt, template, user_input)
        sanitized_messages = [
            message.model_copy(update={"content": redact_for_external_processing(message.content)})
            for message in original_messages
        ]
        findings = _findings_for_messages(original_messages)
        finding_categories = sorted({finding.category for finding in findings})
        redacted_fields = [
            f"messages[{index}].content"
            for index, (original, sanitized) in enumerate(
                zip(original_messages, sanitized_messages, strict=True)
            )
            if original.content != sanitized.content
        ]
        provider = _provider_label(base_url)
        payload_digest = _approval_digest(
            {
                "base_url": base_url.rstrip("/"),
                "model": model,
                "scope_label": scope_label,
                "expected_call_count": expected_call_count,
                "original_messages": [message.model_dump() for message in original_messages],
                "sanitized_messages": [message.model_dump() for message in sanitized_messages],
            }
        )
        approval_digest = approval_digest_override or payload_digest
        warnings = [
            "Detector findings are advisory warnings, not classification decisions.",
            (
                "Review the selected preview and confirm you are authorized to send it "
                "to the configured external provider."
            ),
        ]
        if expected_call_count > 1:
            warnings.append(
                f"This approval covers up to {expected_call_count} external calls in the named chain. "
                "Generated assessments will be rescanned and passed to later steps using the selected disclosure mode."
            )
        return ExternalProcessingPreview(
            required=True,
            external_available=True,
            provider=provider,
            model=model,
            expected_call_count=expected_call_count,
            scope_label=scope_label,
            original_preview=original_messages,
            sanitized_preview=sanitized_messages,
            findings=findings,
            finding_categories=finding_categories,
            redacted_fields=redacted_fields,
            approval_digest=approval_digest,
            payload_digest=payload_digest,
            warnings=warnings,
        )

    def authorize(
        self,
        preview: ExternalProcessingPreview,
        approval: ExternalProcessingApproval | None,
    ) -> ApprovedExternalPayload | None:
        if not preview.external_available or not preview.required:
            return None
        if approval is None:
            raise ExternalProcessingApprovalRequiredError(preview, "External processing approval is required.")
        if approval.disclosure_mode is DisclosureMode.local_only:
            return None
        if approval.approval_digest != preview.approval_digest:
            raise ExternalProcessingApprovalRequiredError(
                preview,
                "The approved preview is stale. Review the current outbound content before sending.",
            )
        acknowledged = set(approval.acknowledged_finding_categories)
        missing = sorted(set(preview.finding_categories) - acknowledged)
        if missing:
            raise ExternalProcessingApprovalRequiredError(
                preview,
                f"Acknowledge the current warning categories before sending: {', '.join(missing)}.",
            )

        messages = (
            preview.sanitized_preview
            if approval.disclosure_mode is DisclosureMode.sanitized
            else preview.original_preview
        )
        return ApprovedExternalPayload(
            messages=messages,
            disclosure_mode=approval.disclosure_mode,
            approval_digest=preview.approval_digest or "",
            finding_categories=preview.finding_categories,
        )


def build_scenario_messages(
    system_prompt: str,
    template: str,
    user_input: str,
) -> list[ExternalProcessingMessage]:
    return [
        ExternalProcessingMessage(
            role="system",
            content=(
                f"{system_prompt}\n\n"
                "Populate the response contract below using facts from the user's scenario input. "
                "If the scenario does not contain information for a field, note the gap explicitly "
                "(for example, 'Not specified in scenario — requires collection'). "
                "Return only the requested JSON object without commentary or extra code fences.\n\n"
                f"TEMPLATE:\n{template}"
            ),
        ),
        ExternalProcessingMessage(role="user", content=user_input),
    ]


def _findings_for_messages(messages: list[ExternalProcessingMessage]) -> list[ExternalProcessingFinding]:
    findings: list[ExternalProcessingFinding] = []
    for index, message in enumerate(messages):
        field_path = f"messages[{index}].content"
        for category in external_processing_categories(message.content):
            if category == "pii":
                findings.append(
                    ExternalProcessingFinding(
                        category=category,
                        severity=ExternalProcessingSeverity.medium,
                        message="Potential PII pattern detected. Review whether it is needed for this provider.",
                        field_path=field_path,
                    )
                )
            else:
                findings.append(
                    ExternalProcessingFinding(
                        category=category,
                        severity=ExternalProcessingSeverity.high,
                        message=(
                            "Potential sensitive-content pattern detected. The detector cannot determine "
                            "classification or whether this is harmless training material."
                        ),
                        field_path=field_path,
                    )
                )
    return findings


def build_chain_approval_digest(
    *,
    base_url: str,
    model: str,
    scenario: str,
    steps: list[dict[str, object]],
    context: dict[str, object],
) -> str:
    return _approval_digest(
        {
            "base_url": base_url.rstrip("/"),
            "model": model,
            "scenario": scenario,
            "steps": steps,
            "context": context,
            "generated_handoff_rule": "rescan-and-apply-approved-disclosure-mode",
        }
    )


def _approval_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _provider_label(base_url: str) -> str:
    parsed = urlparse(base_url)
    return parsed.netloc or parsed.path or "configured provider"
