from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import app.services.external_processing.audit_store as audit_store_module
from app.core.config import get_settings
from app.core.security import external_processing_categories, redact_for_external_processing
from app.main import app
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
)
from app.services.llm_client import _llm_settings


def test_local_only_decision_needs_no_digest_or_acknowledgement() -> None:
    approval = ExternalProcessingApproval(disclosure_mode=DisclosureMode.local_only)

    assert approval.approval_digest is None
    assert approval.acknowledged is False


def test_external_decision_requires_digest() -> None:
    with pytest.raises(ValidationError, match="approval digest"):
        ExternalProcessingApproval(
            disclosure_mode=DisclosureMode.sanitized,
            acknowledged=True,
        )


def test_external_decision_requires_acknowledgement() -> None:
    with pytest.raises(ValidationError, match="explicit acknowledgement"):
        ExternalProcessingApproval(
            disclosure_mode=DisclosureMode.original,
            approval_digest="a" * 64,
        )


def test_external_decision_accepts_original_after_acknowledgement() -> None:
    approval = ExternalProcessingApproval(
        disclosure_mode=DisclosureMode.original,
        approval_digest="b" * 64,
        acknowledged_finding_categories=["pii", "sensitive_content"],
        acknowledged=True,
    )

    assert approval.disclosure_mode is DisclosureMode.original


def test_external_redaction_covers_pii_and_sensitive_patterns() -> None:
    text = "Scenario contains CUI and phone: 703-555-0199."

    redacted = redact_for_external_processing(text)

    assert "CUI" not in redacted
    assert "703-555-0199" not in redacted
    assert "[REDACTED-SENSITIVE]" in redacted
    assert "[REDACTED-PHONE]" in redacted
    assert external_processing_categories(text) == ["sensitive_content", "pii"]


def test_external_warning_categories_are_advisory_data() -> None:
    approval = ExternalProcessingApproval(
        disclosure_mode=DisclosureMode.original,
        approval_digest="c" * 64,
        acknowledged_finding_categories=external_processing_categories("COMSEC training scenario"),
        acknowledged=True,
    )

    assert approval.acknowledged_finding_categories == ["sensitive_content"]


def _build_preview(
    service: ExternalProcessingPreflightService | None = None,
    *,
    user_input: str = "Exercise in Japan.",
) -> ExternalProcessingPreview:
    return (service or ExternalProcessingPreflightService()).build_preview(
        system_prompt="Use only the scenario facts.",
        template="PACE plan for CUI training scenario and phone: 703-555-0199.",
        user_input=user_input,
        base_url="https://api.example.test/v1",
        model="example-model",
        scope_label="agent:staff-s6",
        external_available=True,
    )


def test_preflight_builds_original_and_sanitized_previews() -> None:
    preview = _build_preview()

    assert preview.required is True
    assert preview.provider == "api.example.test"
    assert preview.approval_digest is not None
    assert preview.payload_digest == preview.approval_digest
    assert preview.finding_categories == ["pii", "sensitive_content"]
    assert "703-555-0199" in preview.original_preview[0].content
    assert "703-555-0199" not in preview.sanitized_preview[0].content


def test_preflight_digest_is_stable_and_changes_with_content() -> None:
    service = ExternalProcessingPreflightService()
    first = _build_preview(service)
    second = _build_preview(service)
    changed = _build_preview(service, user_input="Exercise in Norway.")

    assert first.approval_digest == second.approval_digest
    assert first.approval_digest != changed.approval_digest


def test_preflight_requires_current_acknowledged_categories() -> None:
    service = ExternalProcessingPreflightService()
    preview = _build_preview(service)
    approval = ExternalProcessingApproval(
        disclosure_mode=DisclosureMode.original,
        approval_digest=preview.approval_digest,
        acknowledged=True,
    )

    with pytest.raises(ExternalProcessingApprovalRequiredError, match="Acknowledge"):
        service.authorize(preview, approval)


def test_preflight_authorizes_original_or_sanitized_payload() -> None:
    service = ExternalProcessingPreflightService()
    preview = _build_preview(service)
    common = {
        "approval_digest": preview.approval_digest,
        "acknowledged_finding_categories": preview.finding_categories,
        "acknowledged": True,
    }

    original = service.authorize(
        preview,
        ExternalProcessingApproval(disclosure_mode=DisclosureMode.original, **common),
    )
    sanitized = service.authorize(
        preview,
        ExternalProcessingApproval(disclosure_mode=DisclosureMode.sanitized, **common),
    )

    assert original is not None
    assert sanitized is not None
    assert "703-555-0199" in original.messages[0].content
    assert "703-555-0199" not in sanitized.messages[0].content


def test_local_only_approval_returns_no_external_payload() -> None:
    service = ExternalProcessingPreflightService()
    preview = _build_preview(service)

    payload = service.authorize(
        preview,
        ExternalProcessingApproval(disclosure_mode=DisclosureMode.local_only),
    )

    assert payload is None


def test_audit_store_caps_entries_and_never_receives_prompt_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit_store_module, "MAX_AUDIT_ENTRIES", 3)
    store = ExternalProcessingAuditStore(tmp_path)
    for index in range(6):
        store.append(
            "capt-example",
            ExternalProcessingAuditEntry(
                scope_label=f"agent:{index}",
                user_key_digest="replaced-by-store",
                provider="api.example.test",
                model="example-model",
                disclosure_mode=DisclosureMode.sanitized,
                finding_categories=["pii"],
                approval_digest="d" * 64,
                payload_digest="e" * 64,
                expected_call_count=1,
                completed_call_count=1,
                outcome=ExternalProcessingOutcome.completed,
            ),
        )

    log = store.get("capt-example")
    serialized = json.dumps(log.model_dump(mode="json"))

    assert len(log.entries) == 3
    assert log.entries[0].scope_label == "agent:3"
    assert "synthetic prompt marker" not in serialized
    assert '"content"' not in serialized
    assert '"api_key"' not in serialized
    assert '"authorization"' not in serialized
    assert '"response"' not in serialized


@pytest.fixture
def configured_llm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[None, None, None]:
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "example-model")
    monkeypatch.setenv("EXTERNAL_PROCESSING_AUDITS_STORAGE_DIR", str(tmp_path / "audits"))
    get_settings.cache_clear()
    _llm_settings.cache_clear()
    yield
    get_settings.cache_clear()
    _llm_settings.cache_clear()


def test_agent_route_requires_preview_bound_approval(configured_llm: None) -> None:
    client = TestClient(app)
    scenario = "A magnitude 7 earthquake exercise in Japan includes phone: 703-555-0199."

    preview_response = client.post(
        "/agents/staff-g9/external-processing-preview",
        json={"input": scenario, "context": {"request_is_training_or_fictional": True}},
    )
    run_response = client.post(
        "/agents/staff-g9/run",
        json={"input": scenario, "context": {"request_is_training_or_fictional": True}},
    )

    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["required"] is True
    assert preview["approval_digest"]
    assert preview["finding_categories"] == ["pii"]
    assert run_response.status_code == 409
    assert run_response.json()["detail"]["preview"]["approval_digest"] == preview["approval_digest"]


@patch("app.services.llm_client.httpx.Client")
def test_agent_route_sends_sanitized_preview_after_acknowledgement(
    mock_client_cls: MagicMock,
    configured_llm: None,
) -> None:
    client = TestClient(app)
    scenario = "A magnitude 7 earthquake exercise in Japan includes phone: 703-555-0199."
    preview = client.post(
        "/agents/staff-g9/external-processing-preview",
        json={"input": scenario, "context": {"request_is_training_or_fictional": True}},
    ).json()
    response = MagicMock()
    response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "answer": "Approved civil assessment",
                            "scenario_output": {
                                "role": "g9",
                                "civil_situation": {"area": "Japan"},
                            },
                        }
                    )
                }
            }
        ]
    }
    http_client = MagicMock()
    http_client.__enter__.return_value = http_client
    http_client.__exit__.return_value = False
    http_client.post.return_value = response
    mock_client_cls.return_value = http_client

    run_response = client.post(
        "/agents/staff-g9/run",
        json={
            "input": scenario,
            "context": {
                "request_is_training_or_fictional": True,
                "user_key": "route-test",
            },
            "external_processing_approval": {
                "disclosure_mode": "sanitized",
                "approval_digest": preview["approval_digest"],
                "acknowledged_finding_categories": preview["finding_categories"],
                "acknowledged": True,
            },
        },
    )

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["answer"] == "Approved civil assessment"
    assert payload["scenario_output_status"] == "validated"
    sent_body = http_client.post.call_args.kwargs["json"]
    assert "703-555-0199" not in sent_body["messages"][1]["content"]
    assert "[REDACTED-PHONE]" in sent_body["messages"][1]["content"]


def test_chain_preview_uses_one_workflow_digest(configured_llm: None) -> None:
    response = TestClient(app).post(
        "/agents/chain/external-processing-preview",
        json={
            "scenario": "A magnitude 7 earthquake exercise in Japan.",
            "steps": [{"agent_id": "staff-g9"}, {"agent_id": "staff-s2"}],
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    preview = response.json()
    assert preview["scope_label"] == "chain:staff-g9->staff-s2"
    assert preview["expected_call_count"] == 2
    assert preview["approval_digest"]
    assert preview["payload_digest"]
