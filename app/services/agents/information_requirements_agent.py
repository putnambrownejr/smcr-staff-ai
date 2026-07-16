"""Decision-linked Information Requirements Manager."""

from __future__ import annotations

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, ScenarioOutputStatus, StructuredCitation
from app.schemas.scenario_handoff import InformationRequirement, InformationRequirementsScenarioOutput
from app.schemas.source_state import SourceTrustMarker
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import S2_REFERENCES, citation_titles, source_trust_markers, structured_citations

_DRAFT_WARNING = "DRAFT — Verify all references against current official sources before acting."


class InformationRequirementsManagerAgent(Agent):
    """Turns a planning question into a human-reviewable IR register."""

    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="information-requirements-manager",
            name="Information Requirements Manager",
            description="Builds a decision-linked PIR, FFIR, and CIR register from public, local, training, or fictional planning inputs.",
            domain="information requirements management",
            intended_users=["command teams", "planners", "S-2/G-2", "S-3", "G-9/civil affairs"],
            allowed_sources=["user-selected saved local public sources", "public doctrine", "training or fictional scenario material"],
            disallowed_inputs=["classified or controlled information", "real collection tasking", "sensitive movements or COMSEC", "individual targeting"],
            system_prompt=("Create advisory PIR, FFIR, and CIR recommendations tied to a decision. Do not issue collection tasking " "or claim authority. Mark missing evidence and ownership as human-review requirements."),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        area_study = _assessment(context, "area_study")
        actor_network = _assessment(context, "actor_network")
        evidence = _source_evidence(context)
        decision = _decision_from_input(input_text)
        requirements = _requirements(decision, area_study, actor_network)
        output = InformationRequirementsScenarioOutput(requirements=requirements, evidence_gaps=_gaps(area_study, actor_network, evidence))
        local_citations = _local_citations(evidence)
        return self._response(
            answer=_render_answer(output, decision, area_study, actor_network),
            input_text=input_text,
            citations=[*citation_titles(S2_REFERENCES), *[citation.title for citation in local_citations]],
            structured_citations=[*structured_citations(S2_REFERENCES), *local_citations],
            source_trust=[*source_trust_markers(S2_REFERENCES), *_local_source_trust(context)],
            confidence=Confidence.low,
            follow_up_questions=["What commander decision and decision deadline does each requirement support?", "Which approved source or scenario-control input can validate each indicator?", "Who will a human assign as the responsible staff owner?"],
            scenario_output=output.model_dump(),
            scenario_output_status=ScenarioOutputStatus.validated,
        )


def build_information_requirements_agent() -> InformationRequirementsManagerAgent:
    return InformationRequirementsManagerAgent()


def _assessment(context: AgentContext, role: str) -> dict[str, object]:
    value = context.prior_assessments.get(role)
    return value if isinstance(value, dict) else {}


def _source_evidence(context: AgentContext) -> list[dict[str, str]]:
    raw = context.extra.get("source_evidence")
    return [{str(k): str(v) for k, v in item.items() if v is not None} for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []


def _decision_from_input(input_text: str) -> str:
    return f"Commander planning decision described in request: {input_text.strip()}"


def _requirements(decision: str, area_study: dict[str, object], actor_network: dict[str, object]) -> list[InformationRequirement]:
    area_signal = "Which area-study factor or civil/infrastructure constraint would change the decision?" if area_study else "What operational-area, civil, or infrastructure factor must be validated before the decision?"
    actor_signal = "Which organization-level relationship or influence pattern would change the decision?" if actor_network else "Which organization-level actor or relationship must be validated before the decision?"
    return [
        InformationRequirement(category="PIR", requirement=actor_signal, decision_supported=decision, indicator="Approved source or scenario evidence confirms a relevant organization-level relationship.", collection_question=actor_signal, recommended_owner="Human assignment required (S-2/G-2 lead recommendation)", priority="High"),
        InformationRequirement(category="FFIR", requirement="What own-force readiness, access, or support constraint would prevent the selected option?", decision_supported=decision, indicator="Validated readiness, access, or support status changes the feasible option.", collection_question="Which readiness or support condition must be confirmed before the decision?", recommended_owner="Human assignment required (operations/logistics lead recommendation)", priority="High"),
        InformationRequirement(category="CIR", requirement=area_signal, decision_supported=decision, indicator="Approved evidence confirms a civil, population, infrastructure, or institutional factor affecting the decision.", collection_question=area_signal, recommended_owner="Human assignment required (G-9/civil lead recommendation)", priority="Medium"),
    ]


def _gaps(area_study: dict[str, object], actor_network: dict[str, object], evidence: list[dict[str, str]]) -> list[str]:
    gaps = ["Validate each requirement's indicator, responsible owner, and decision deadline before issuing any tasking."]
    if not area_study:
        gaps.append("No prior area-study output supplied; civil and infrastructure requirements remain provisional.")
    if not actor_network:
        gaps.append("No prior actor-network output supplied; organization-level PIR remains provisional.")
    else:
        network_gaps = actor_network.get("evidence_gaps")
        if isinstance(network_gaps, list):
            for gap in network_gaps[:2]:
                if isinstance(gap, str) and gap.strip():
                    gaps.append(f"Inherited actor-network gap: {gap}")
    if not evidence:
        gaps.append("No local source evidence attached or retrieved; requirements are planning recommendations only.")
    return gaps


def _local_citations(evidence: list[dict[str, str]]) -> list[StructuredCitation]:
    return [StructuredCitation(title=item.get("title", "Saved local source"), url=item.get("url") or None, publisher=item.get("publisher") or None, retrieved_at=item.get("retrieved_at") or None, source_hash=item.get("source_hash") or None, chunk_id=item.get("chunk_id") or None, confidence=Confidence.low, notes=f"Local source evidence; trust_status={item.get('trust_status', 'unknown')}.") for item in evidence]


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


def _render_answer(output: InformationRequirementsScenarioOutput, decision: str, area_study: dict[str, object], actor_network: dict[str, object]) -> str:
    entries = "\n".join(f"- {item.category}: {item.requirement}\n  Decision supported: {item.decision_supported}\n  Indicator: {item.indicator}\n  Collection question: {item.collection_question}\n  Recommended owner: {item.recommended_owner}\n  Priority: {item.priority}" for item in output.requirements)
    upstream = f"Area study: {'received' if area_study else 'not supplied'}; actor network: {'received' if actor_network else 'not supplied'}."
    return ("Information Requirements Manager — advisory decision register\n\n" f"Decision framing:\n- {decision}\n\nUpstream context: {upstream}\n\nRequirements:\n{entries}\n\n" "Evidence gaps and human-review gates:\n" + "\n".join(f"- {gap}" for gap in output.evidence_gaps) + "\n\n" "These are recommendations for human review, not collection tasking or authority.\n\n" + _DRAFT_WARNING)
