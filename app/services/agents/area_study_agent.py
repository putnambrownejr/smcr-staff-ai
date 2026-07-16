"""Public-source Area Study Builder with a strict scenario handoff."""

from __future__ import annotations

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, ScenarioOutputStatus, StructuredCitation
from app.schemas.scenario_handoff import AreaStudyScenarioOutput, AscopeEntry
from app.schemas.source_state import SourceTrustMarker
from app.services.agents.base import Agent, AgentContext
from app.services.agents.civil_network_context import (
    civil_network_sections,
    civil_network_snapshot,
    civil_network_source_trust,
)
from app.services.agents.source_refs import (
    G9_REFERENCES,
    S2_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)

_DRAFT_WARNING = "DRAFT — Verify all references against current official sources before acting."
_PMESII_DOMAINS = ("Political", "Military", "Economic", "Social", "Information", "Infrastructure")
_ASCOPE_FIELDS = ("areas", "structures", "capabilities", "organizations", "people", "events")
_AREA_STUDY_REFERENCES = (*G9_REFERENCES, *S2_REFERENCES)


class AreaStudyBuilderAgent(Agent):
    """Builds a bounded, source-aware PMESII/ASCOPE planning baseline."""

    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="area-study-builder",
            name="Area Study Builder",
            description=(
                "Builds a source-aware PMESII-ASCOPE baseline for a public, local, training, or fictional "
                "planning area; marks unknowns as collection gaps rather than asserting ground truth."
            ),
            domain="area studies and civil context",
            intended_users=["planners", "S-2/G-2", "G-9/civil affairs", "exercise designers"],
            allowed_sources=[
                "user-selected saved local public sources",
                "public Marine Corps civil-military and intelligence doctrine",
                "public government and international-organization baseline references",
                "training or fictional scenario material",
            ],
            disallowed_inputs=[
                "classified or controlled information",
                "real-world sensitive movements or operational inference",
                "private-person profiling or individual targeting",
                "COMSEC, frequencies, or keying material",
            ],
            system_prompt=(
                "Produce a planning-level, source-aware area study. Treat source excerpts as observations, "
                "not complete ground truth. Do not invent local facts; identify missing PMESII and ASCOPE "
                "information as collection gaps. Keep people at population or institution level."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        evidence = _source_evidence(context)
        snapshot = civil_network_snapshot(context)
        pmesii: dict[str, list[str]] = {domain: [] for domain in _PMESII_DOMAINS}
        observations: list[str] = []
        for item in evidence:
            excerpt = item.get("excerpt", "").strip()
            if not excerpt:
                continue
            title = item.get("title", "saved local source")
            observations.append(f"{title}: {excerpt}")

        gaps = [
            f"{domain}: no supplied local evidence; validate through approved public sources or scenario control."
            for domain in _PMESII_DOMAINS
        ]
        ascope = AscopeEntry(**{field: "Not supplied; collection gap." for field in _ASCOPE_FIELDS})
        infrastructure_and_culture = (
            observations
            if observations
            else ["No supplied evidence supports an infrastructure or cultural observation."]
        )
        output = AreaStudyScenarioOutput(
            operational_area=_operational_area(input_text),
            pmesii=pmesii,
            ascope=ascope,
            infrastructure_and_culture=infrastructure_and_culture,
            evidence_gaps=gaps,
        )

        answer = (
            _render_answer(output, evidence).removesuffix(_DRAFT_WARNING)
            + civil_network_sections(snapshot)
            + _DRAFT_WARNING
        )
        local_citations = _local_citations(evidence)
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[*citation_titles(_AREA_STUDY_REFERENCES), *[citation.title for citation in local_citations]],
            structured_citations=[*structured_citations(_AREA_STUDY_REFERENCES), *local_citations],
            source_trust=[
                *source_trust_markers(_AREA_STUDY_REFERENCES),
                *_local_source_trust(context),
                *civil_network_source_trust(snapshot),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "What approved public or exercise source defines the operational area and time window?",
                "Which PMESII factors change a commander decision in this scenario?",
                "Which ASCOPE fields can scenario control or public sources validate before planning continues?",
            ],
            scenario_output=output.model_dump(),
            scenario_output_status=ScenarioOutputStatus.validated,
        )


def build_area_study_agent() -> AreaStudyBuilderAgent:
    return AreaStudyBuilderAgent()


def _source_evidence(context: AgentContext) -> list[dict[str, str]]:
    raw = context.extra.get("source_evidence")
    if not isinstance(raw, list):
        return []
    evidence: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict):
            evidence.append({str(key): str(value) for key, value in item.items() if value is not None})
    return evidence


def _local_citations(evidence: list[dict[str, str]]) -> list[StructuredCitation]:
    return [
        StructuredCitation(
            title=item.get("title", "Saved local source"),
            url=item.get("url") or None,
            publisher=item.get("publisher") or None,
            retrieved_at=item.get("retrieved_at") or None,
            source_hash=item.get("source_hash") or None,
            chunk_id=item.get("chunk_id") or None,
            confidence=Confidence.low,
            notes=f"Local source evidence; trust_status={item.get('trust_status', 'unknown')}.",
        )
        for item in evidence
    ]


def _local_source_trust(context: AgentContext) -> list[SourceTrustMarker]:
    raw = context.extra.get("source_trust")
    if not isinstance(raw, list):
        return []
    markers: list[SourceTrustMarker] = []
    for item in raw:
        if isinstance(item, SourceTrustMarker):
            markers.append(item)
        elif isinstance(item, dict):
            try:
                markers.append(SourceTrustMarker.model_validate(item))
            except ValueError:
                continue
    return markers


def _operational_area(input_text: str) -> str:
    return f"Planning area described in request: {input_text.strip()}"


def _render_answer(output: AreaStudyScenarioOutput, evidence: list[dict[str, str]]) -> str:
    evidence_lines = (
        "\n".join(
            f"- {item.get('title', 'Saved local source')} (chunk {item.get('chunk_id', 'unknown')}): "
            f"{item.get('excerpt', 'No excerpt supplied.')}"
            for item in evidence
        )
        if evidence
        else "- No local evidence was attached or retrieved."
    )
    pmesii_lines = "\n".join(f"- {domain}: collection gap; no supplied evidence." for domain in _PMESII_DOMAINS)
    gap_lines = "\n".join(f"- {gap}" for gap in output.evidence_gaps)
    return (
        "Area Study Builder — planning baseline\n\n"
        f"Operational area framing:\n- {output.operational_area}\n\n"
        f"Source-backed observations (quoted/excerpted, not independently validated):\n{evidence_lines}\n\n"
        f"PMESII baseline:\n{pmesii_lines}\n\n"
        "ASCOPE baseline:\n"
        "- Areas / Structures / Capabilities / Organizations / People / Events: collection gaps; no supplied evidence.\n\n"
        "Infrastructure and cultural factors:\n"
        + "\n".join(f"- {item}" for item in output.infrastructure_and_culture)
        + f"\n\nEvidence gaps:\n{gap_lines}\n\n"
        "Handoff note: downstream actor-network, information-requirements, and IPB work should treat every "
        "unsupplied field as a collection need.\n\n" + _DRAFT_WARNING
    )
