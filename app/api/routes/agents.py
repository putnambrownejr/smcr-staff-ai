from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.agents import AgentMetadata, AgentRunRequest, AgentRunResponse, ScenarioOutputStatus, SourceSelection
from app.schemas.external_processing import DisclosureMode, ExternalProcessingApproval, ExternalProcessingPreview
from app.schemas.roundtable import RoundtableRequest, RoundtableResponse
from app.schemas.scenario_handoff import ChainRequest, ChainResponse, ChainStepResult
from app.schemas.source_state import SourceTrustMarker
from app.services.agents.base import Agent, AgentContext
from app.services.agents.registry import agent_registry
from app.services.agents.roundtable import RoundtableService, resolve_participants
from app.services.agents.source_context import SourceEvidenceResolver
from app.services.external_processing.preflight import (
    ExternalProcessingApprovalRequiredError,
    ExternalProcessingPreviewReadyError,
    build_chain_approval_digest,
)
from app.services.session.active_context_store import ActiveUserContextStore
from app.services.source_library.store import SourceLibraryStore

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[LocalApiKeyDependency])

_PUBLIC_CONTEXT_KEYS = {
    "user_key",
    "user_role",
    "unit_id",
    "request_is_training_or_fictional",
    "extra",
    "prior_assessments",
}


def get_active_context_store() -> Iterator[ActiveUserContextStore]:
    settings = get_settings()
    yield ActiveUserContextStore(settings.active_user_context_storage_dir)


def get_source_evidence_resolver() -> SourceEvidenceResolver:
    """Provide a local-only resolver for already-approved Source Library content."""
    settings = get_settings()
    return SourceEvidenceResolver(SourceLibraryStore(settings.source_library_storage_dir))


@router.get("", response_model=list[AgentMetadata])
def list_agents() -> list[AgentMetadata]:
    return agent_registry.list_metadata()


@router.post("/chain/external-processing-preview", response_model=ExternalProcessingPreview)
def preview_chain_external_processing(
    request: ChainRequest,
    active_context_store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
    source_evidence_resolver: Annotated[SourceEvidenceResolver, Depends(get_source_evidence_resolver)],
) -> ExternalProcessingPreview:
    scope_label = "chain:" + "->".join(step.agent_id for step in request.steps)
    for step in request.steps:
        if agent_registry.get(step.agent_id) is None:
            raise HTTPException(status_code=404, detail=f"Unknown agent in chain: {step.agent_id}")
    if not get_settings().llm_api_key:
        return _no_external_preview(scope_label, "No external LLM is configured; execution remains local-only.")
    try:
        _run_agent_chain(request, active_context_store, source_evidence_resolver, preview_only=True)
    except ExternalProcessingPreviewReadyError as exc:
        return exc.preview
    return _no_external_preview("chain", "The requested chain does not use external scenario inference.")


@router.post("/roundtable/external-processing-preview", response_model=ExternalProcessingPreview)
def preview_roundtable_external_processing(
    request: RoundtableRequest,
    active_context_store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
) -> ExternalProcessingPreview:
    participants, _, agents = _resolve_roundtable_agents(request)
    scope_label = _roundtable_scope_label(participants, request.synthesizer)
    if not get_settings().llm_api_key:
        return _no_external_preview(scope_label, "No external LLM is configured; execution remains local-only.")
    try:
        _run_roundtable(request, active_context_store, preview_only=True)
    except ExternalProcessingPreviewReadyError as exc:
        return exc.preview
    return _no_external_preview(scope_label, "The requested round table does not use external scenario inference.")


@router.post("/roundtable", response_model=RoundtableResponse)
def run_roundtable(
    request: RoundtableRequest,
    active_context_store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
) -> RoundtableResponse:
    """Run a virtual staff round table: concurrent assessments, cross-review, synthesis."""
    try:
        return _run_roundtable(request, active_context_store)
    except ExternalProcessingApprovalRequiredError as exc:
        raise _approval_http_error(exc) from exc


def _resolve_roundtable_agents(
    request: RoundtableRequest,
) -> tuple[list[str], list[str], dict[str, Agent]]:
    participants, auto_selected = resolve_participants(request.scenario, request.agents, request.synthesizer)
    if not participants:
        raise HTTPException(status_code=422, detail="No participants resolved for the round table.")
    agents: dict[str, Agent] = {}
    agent_ids = [*participants, *([request.synthesizer] if request.synthesizer else [])]
    for agent_id in agent_ids:
        agent = agent_registry.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Unknown agent in round table: {agent_id}")
        agents[agent_id] = agent
    return participants, auto_selected, agents


def _roundtable_scope_label(participants: list[str], synthesizer: str | None) -> str:
    label = "roundtable:" + "+".join(participants)
    if synthesizer:
        label += f"->{synthesizer}"
    return label


def _run_roundtable(
    request: RoundtableRequest,
    active_context_store: ActiveUserContextStore,
    *,
    preview_only: bool = False,
) -> RoundtableResponse:
    participants, auto_selected, agents = _resolve_roundtable_agents(request)
    settings = get_settings()
    scope_label = _roundtable_scope_label(participants, request.synthesizer)
    agent_ids = [*participants, *([request.synthesizer] if request.synthesizer else [])]
    roundtable_digest = build_chain_approval_digest(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        scenario=request.scenario,
        steps=[{"agent_id": agent_id} for agent_id in agent_ids],
        context={**request.context, "roundtable_rounds": request.rounds},
    )
    expected_call_count = len(participants) * request.rounds + (1 if request.synthesizer else 0)

    def context_factory(prior_assessments: dict[str, object]) -> AgentContext:
        return _build_agent_context(
            request.context,
            active_context_store,
            approval=request.external_processing_approval,
            preview_only=preview_only,
            scope_label=scope_label,
            expected_call_count=expected_call_count,
            approval_digest_override=roundtable_digest,
            prior_assessments=prior_assessments,
        )

    return RoundtableService(agents).run(
        request,
        context_factory,
        participants,
        auto_selected,
        preview_only=preview_only,
    )


@router.post("/{agent_id}/external-processing-preview", response_model=ExternalProcessingPreview)
def preview_agent_external_processing(
    agent_id: str,
    request: AgentRunRequest,
    active_context_store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
    source_evidence_resolver: Annotated[SourceEvidenceResolver, Depends(get_source_evidence_resolver)],
) -> ExternalProcessingPreview:
    agent = agent_registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    if not get_settings().llm_api_key:
        return _no_external_preview(
            f"agent:{agent_id}",
            "No external LLM is configured; execution remains local-only.",
        )
    context = _build_agent_context(
        request.context,
        active_context_store,
        options=request.options,
        source_selection=request.source_selection,
        source_evidence_resolver=source_evidence_resolver,
        approval=None,
        preview_only=True,
        scope_label=f"agent:{agent_id}",
    )
    try:
        agent.run(request.input, context)
    except ExternalProcessingPreviewReadyError as exc:
        return exc.preview
    return _no_external_preview(f"agent:{agent_id}", "This request does not use external scenario inference.")


@router.post("/{agent_id}/run", response_model=AgentRunResponse)
def run_agent(
    agent_id: str,
    request: AgentRunRequest,
    active_context_store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
    source_evidence_resolver: Annotated[SourceEvidenceResolver, Depends(get_source_evidence_resolver)],
) -> AgentRunResponse:
    agent = agent_registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    context = _build_agent_context(
        request.context,
        active_context_store,
        options=request.options,
        source_selection=request.source_selection,
        source_evidence_resolver=source_evidence_resolver,
        approval=request.external_processing_approval,
        scope_label=f"agent:{agent_id}",
    )
    try:
        return _apply_source_context(agent.run(request.input, context), context)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ExternalProcessingApprovalRequiredError as exc:
        raise _approval_http_error(exc) from exc


@router.post("/chain", response_model=ChainResponse)
def run_agent_chain(
    request: ChainRequest,
    active_context_store: Annotated[ActiveUserContextStore, Depends(get_active_context_store)],
    source_evidence_resolver: Annotated[SourceEvidenceResolver, Depends(get_source_evidence_resolver)],
) -> ChainResponse:
    """Run agents in sequence, passing structured scenario output forward."""
    try:
        return _run_agent_chain(request, active_context_store, source_evidence_resolver)
    except ExternalProcessingApprovalRequiredError as exc:
        raise _approval_http_error(exc) from exc


def _run_agent_chain(
    request: ChainRequest,
    active_context_store: ActiveUserContextStore,
    source_evidence_resolver: SourceEvidenceResolver,
    *,
    preview_only: bool = False,
) -> ChainResponse:
    prior_assessments: dict[str, object] = {}
    results: list[ChainStepResult] = []
    warnings: list[str] = []
    settings = get_settings()
    scope_label = "chain:" + "->".join(step.agent_id for step in request.steps)
    chain_digest = build_chain_approval_digest(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        scenario=request.scenario,
        steps=[step.model_dump() for step in request.steps],
        context=dict(request.context),
    )

    for step in request.steps:
        agent = agent_registry.get(step.agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Unknown agent in chain: {step.agent_id}")

        context = _build_agent_context(
            request.context,
            active_context_store,
            source_selection=request.source_selection,
            source_evidence_resolver=source_evidence_resolver,
            approval=request.external_processing_approval,
            preview_only=preview_only,
            scope_label=scope_label,
            expected_call_count=len(request.steps),
            approval_digest_override=chain_digest,
            prior_assessments=prior_assessments,
        )
        agent_input = step.input or request.scenario
        response = _apply_source_context(agent.run(agent_input, context), context)

        scenario_output = response.scenario_output
        if scenario_output is not None:
            role_key = str(scenario_output.get("role", step.agent_id))
            prior_assessments[role_key] = scenario_output

        results.append(
            ChainStepResult(
                agent_id=step.agent_id,
                response=response.model_dump(),
                scenario_output=scenario_output,
            )
        )
        warnings.extend(response.warnings)
        external_chain = (
            bool(settings.llm_api_key)
            and request.external_processing_approval is not None
            and request.external_processing_approval.disclosure_mode is not DisclosureMode.local_only
        )
        if external_chain and response.scenario_output_status is ScenarioOutputStatus.invalid:
            reason = f"Structured handoff from {step.agent_id} was invalid; later external calls were not made."
            warnings.append(reason)
            return ChainResponse(
                scenario=request.scenario,
                results=results,
                warnings=_unique_warnings(warnings),
                completed=False,
                stopped_at_agent_id=step.agent_id,
                stopped_reason=reason,
            )

    return ChainResponse(scenario=request.scenario, results=results, warnings=_unique_warnings(warnings))


def _unique_warnings(warnings: list[str]) -> list[str]:
    return list(dict.fromkeys(warnings))


def _build_agent_context(
    raw_context: dict[str, object],
    active_context_store: ActiveUserContextStore,
    *,
    approval: ExternalProcessingApproval | None,
    preview_only: bool = False,
    scope_label: str,
    expected_call_count: int = 1,
    approval_digest_override: str | None = None,
    prior_assessments: dict[str, object] | None = None,
    options: dict[str, object] | None = None,
    source_selection: SourceSelection | None = None,
    source_evidence_resolver: SourceEvidenceResolver | None = None,
) -> AgentContext:
    context_payload = {key: value for key, value in raw_context.items() if key in _PUBLIC_CONTEXT_KEYS}
    unknown_context = {key: value for key, value in raw_context.items() if key not in _PUBLIC_CONTEXT_KEYS}
    raw_extra = context_payload.get("extra")
    extra = dict(raw_extra) if isinstance(raw_extra, dict) else {}
    extra.update(unknown_context)
    if options:
        extra["agent_options"] = dict(options)

    if user_key := context_payload.get("user_key"):
        stored_context = active_context_store.get(str(user_key))
        if stored_context is not None:
            extra["active_user_context"] = stored_context.model_dump(mode="json")

    if source_selection is not None:
        if source_evidence_resolver is None:
            raise RuntimeError("A source selection requires a source evidence resolver.")
        if not isinstance(user_key, str) or not user_key.strip():
            raise HTTPException(status_code=422, detail="Source selection requires context.user_key.")
        try:
            resolved = source_evidence_resolver.resolve(user_key, source_selection)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        extra["source_evidence"] = resolved.items
        extra["source_trust"] = [marker.model_dump(mode="json") for marker in resolved.source_trust]
        extra["source_context_warnings"] = resolved.warnings

    context_payload["extra"] = extra
    if prior_assessments is not None:
        context_payload["prior_assessments"] = prior_assessments
    context_payload.update(
        {
            "external_processing_approval": approval,
            "external_processing_preview_only": preview_only,
            "external_processing_scope_label": scope_label,
            "external_processing_expected_call_count": expected_call_count,
            "external_processing_approval_digest_override": approval_digest_override,
        }
    )
    return AgentContext.model_validate(context_payload)


def _apply_source_context(response: AgentRunResponse, context: AgentContext) -> AgentRunResponse:
    """Expose resolver trust markers and warnings alongside an agent response."""
    raw_trust = context.extra.get("source_trust")
    raw_warnings = context.extra.get("source_context_warnings")
    source_trust = list(response.source_trust)
    if isinstance(raw_trust, list):
        source_trust.extend(
            marker
            for item in raw_trust
            if isinstance(item, dict)
            and (marker := _source_trust_marker(item)) is not None
            and marker not in source_trust
        )
    warnings = list(response.warnings)
    if isinstance(raw_warnings, list):
        warnings.extend(warning for warning in raw_warnings if isinstance(warning, str))
    return response.model_copy(update={"source_trust": source_trust, "warnings": _unique_warnings(warnings)})


def _source_trust_marker(payload: dict[str, object]) -> SourceTrustMarker | None:
    try:
        return SourceTrustMarker.model_validate(payload)
    except ValueError:
        return None


def _approval_http_error(exc: ExternalProcessingApprovalRequiredError) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "reason": exc.reason,
            "preview": exc.preview.model_dump(mode="json"),
        },
    )


def _no_external_preview(scope_label: str, message: str) -> ExternalProcessingPreview:
    settings = get_settings()
    return ExternalProcessingPreview(
        required=False,
        external_available=bool(settings.llm_api_key),
        provider=None,
        model=settings.llm_model if settings.llm_api_key else None,
        expected_call_count=0,
        scope_label=scope_label,
        warnings=[message],
    )
