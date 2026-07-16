"""Bounded IPB Assistant for public, local, training, and fictional planning."""

from __future__ import annotations

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, ScenarioOutputStatus, StructuredCitation
from app.schemas.scenario_handoff import IpbScenarioOutput
from app.schemas.source_state import SourceTrustMarker
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import S2_REFERENCES, citation_titles, source_trust_markers, structured_citations

_DRAFT_WARNING = "DRAFT — Verify all references against current official sources before acting."


class IpbAssistantAgent(Agent):
    """Produces a four-step IPB scaffold without asserting unsupplied facts."""

    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="ipb-assistant",
            name="IPB Assistant",
            description=(
                "Builds a source-aware, four-step IPB planning scaffold from public, local, training, or "
                "fictional material; separates evidence, assumptions, hypotheses, indicators, and gaps."
            ),
            domain="intelligence preparation of the battlespace",
            intended_users=["S-2/G-2", "planners", "S-3", "G-9/civil affairs", "exercise designers"],
            allowed_sources=["user-selected saved local public sources", "public doctrine", "training or fictional scenario material"],
            disallowed_inputs=["classified or controlled information", "real-world sensitive movements", "COMSEC or frequencies", "individual targeting"],
            system_prompt=(
                "Create an advisory IPB scaffold only. Use supplied evidence verbatim or as attributed observations; "
                "label all unvalidated inferences as assumptions or hypotheses and all unknowns as collection gaps."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        evidence = _source_evidence(context)
        area_study = _assessment(context, "area_study")
        actor_network = _assessment(context, "actor_network")
        information_requirements = _assessment(context, "information_requirements")
        output = _build_output(area_study, actor_network, information_requirements, evidence)
        local_citations = _local_citations(evidence)
        return self._response(
            answer=_render_answer(output, evidence, area_study, actor_network, information_requirements),
            input_text=input_text,
            citations=[*citation_titles(S2_REFERENCES), *[citation.title for citation in local_citations]],
            structured_citations=[*structured_citations(S2_REFERENCES), *local_citations],
            source_trust=[*source_trust_markers(S2_REFERENCES), *_local_source_trust(context)],
            confidence=Confidence.low,
            follow_up_questions=[
                "Which approved source or scenario-control input validates each environmental factor?",
                "Which hypothesis discriminator matters before the next commander decision?",
                "Which human staff owner will validate the listed collection gaps?",
            ],
            scenario_output=output.model_dump(),
            scenario_output_status=ScenarioOutputStatus.validated,
        )


def build_ipb_assistant_agent() -> IpbAssistantAgent:
    return IpbAssistantAgent()


def _assessment(context: AgentContext, role: str) -> dict[str, object]:
    value = context.prior_assessments.get(role)
    return value if isinstance(value, dict) else {}


def _source_evidence(context: AgentContext) -> list[dict[str, str]]:
    raw = context.extra.get("source_evidence")
    if not isinstance(raw, list):
        return []
    return [{str(key): str(value) for key, value in item.items() if value is not None} for item in raw if isinstance(item, dict)]


def _build_output(
    area_study: dict[str, object],
    actor_network: dict[str, object],
    information_requirements: dict[str, object],
    evidence: list[dict[str, str]],
) -> IpbScenarioOutput:
    environment = [
        "Define the operational environment from approved area-study evidence; no independently validated baseline was supplied."
    ]
    if area_study:
        environment = [f"Upstream area-study framing: {area_study.get('operational_area', 'operational area not specified.')}."]
    effects = ["Environmental effects on friendly or adversary options are not established by supplied evidence."]
    patterns = ["Broad hazard or actor patterns require approved public or scenario evidence; no intent or capability is inferred."]
    if actor_network:
        patterns = ["Upstream actor-network output is a planning hypothesis; validate organization-level relationships before use."]
    indicators = ["Event template: validate the decision-linked PIR, FFIR, and CIR indicators before treating a pattern as confirmed."]
    if information_requirements:
        requirements = information_requirements.get("requirements")
        if isinstance(requirements, list):
            indicators = [
                f"Event template indicator: {item.get('indicator', 'Indicator not provided.')}"
                for item in requirements[:3]
                if isinstance(item, dict)
            ] or indicators
    gaps = ["No supplied evidence confirms terrain, weather, actor intent, capability, disposition, or event timing."]
    for assessment, label in ((area_study, "area-study"), (actor_network, "actor-network"), (information_requirements, "information-requirements")):
        if not assessment:
            gaps.append(f"No upstream {label} handoff supplied.")
    if not evidence:
        gaps.append("No local source evidence attached or retrieved; this is a collection scaffold only.")
    return IpbScenarioOutput(
        operational_environment=environment,
        environmental_effects=effects,
        broad_threat_or_hazard_patterns=patterns,
        indicators_and_event_templates=indicators,
        collection_gaps=gaps,
    )


def _local_citations(evidence: list[dict[str, str]]) -> list[StructuredCitation]:
    return [
        StructuredCitation(
            title=item.get("title", "Saved local source"), url=item.get("url") or None,
            publisher=item.get("publisher") or None, retrieved_at=item.get("retrieved_at") or None,
            source_hash=item.get("source_hash") or None, chunk_id=item.get("chunk_id") or None,
            confidence=Confidence.low, notes=f"Local source evidence; trust_status={item.get('trust_status', 'unknown')}.",
        )
        for item in evidence
    ]


def _local_source_trust(context: AgentContext) -> list[SourceTrustMarker]:
    raw = context.extra.get("source_trust")
    markers: list[SourceTrustMarker] = []
    if isinstance(raw, list):
        for item in raw:
            try:
                markers.append(item if isinstance(item, SourceTrustMarker) else SourceTrustMarker.model_validate(item))
            except ValueError:
                continue
    return markers


def _render_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _render_answer(
    output: IpbScenarioOutput, evidence: list[dict[str, str]], area_study: dict[str, object],
    actor_network: dict[str, object], information_requirements: dict[str, object],
) -> str:
    evidence_lines = _render_list([
        f"{item.get('title', 'Saved local source')} (chunk {item.get('chunk_id', 'unknown')}): {item.get('excerpt', 'No excerpt supplied.')}"
        for item in evidence
    ]) if evidence else "- No local evidence was attached or retrieved."
    assumptions = [
        "Upstream handoffs are planning inputs, not independently verified facts.",
        "Any environmental effect not directly supported by a cited source requires human validation.",
    ]
    hypotheses = [
        "Hypothesis: a confirmed environmental or organization-level change may alter the commander decision.",
        "Discriminator: approved evidence validates an IPB indicator or reveals a material collection gap.",
    ]
    upstream = (
        f"Area study: {'received' if area_study else 'not supplied'}; "
        f"actor network: {'received' if actor_network else 'not supplied'}; "
        f"information requirements: {'received' if information_requirements else 'not supplied'}."
    )
    return (
        "IPB Assistant — four-step planning scaffold\n\n"
        f"Upstream handoffs: {upstream}\n\n"
        f"Evidence (source-backed observations only):\n{evidence_lines}\n\n"
        f"Step 1 — Define the operational environment:\n{_render_list(output.operational_environment)}\n\n"
        f"Step 2 — Describe environmental effects:\n{_render_list(output.environmental_effects)}\n\n"
        f"Step 3 — Evaluate broad threat or hazard patterns:\n{_render_list(output.broad_threat_or_hazard_patterns)}\n\n"
        f"Step 4 — Determine indicators and event templates:\n{_render_list(output.indicators_and_event_templates)}\n\n"
        f"Assumptions:\n{_render_list(assumptions)}\n\n"
        f"Hypotheses:\n{_render_list(hypotheses)}\n\n"
        f"Collection gaps:\n{_render_list(output.collection_gaps)}\n\n"
        "This is an advisory planning scaffold, not intelligence collection tasking or a prediction.\n\n"
        + _DRAFT_WARNING
    )
