"""Organization-level Actor Network Analyst with bounded scenario handoff."""

from __future__ import annotations

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, ScenarioOutputStatus, StructuredCitation
from app.schemas.scenario_handoff import ActorNetworkScenarioOutput
from app.schemas.source_state import SourceTrustMarker
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import S2_REFERENCES, citation_titles, source_trust_markers, structured_citations

_DRAFT_WARNING = "DRAFT — Verify all references against current official sources before acting."
# Match individual-targeting/profiling intent without tripping on ordinary staff
# language like "target audience" (IO/civil-affairs) or "target date" (planning).
_TARGETING_TERMS = ("targeting", "individual target", "named civilian", "private person", "individual profile")


class ActorNetworkAnalystAgent(Agent):
    """Maps institutions and broad actor categories, never individual people."""

    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="actor-network-analyst",
            name="Actor Network Analyst",
            description=(
                "Maps organizations, institutions, and broad actor categories for public, local, training, "
                "or fictional planning; records relationship confidence and collection gaps without profiling people."
            ),
            domain="actor network analysis",
            intended_users=["planners", "S-2/G-2", "G-9/civil affairs", "exercise designers"],
            allowed_sources=["user-selected saved local public sources", "public doctrine", "training or fictional scenario material"],
            disallowed_inputs=["individual targeting", "private-person profiling", "classified or controlled information", "sensitive movements or COMSEC"],
            system_prompt=(
                "Map organizations, institutions, and broad categories only. State evidence confidence and gaps. "
                "Do not profile private people, identify targets, or infer real-world operational activity."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        if any(term in input_text.lower() for term in _TARGETING_TERMS):
            return self._safety_response(input_text)

        evidence = _source_evidence(context)
        area_study = _assessment(context, "area_study")
        actors = _actors_from_evidence(evidence)
        relationships = _relationships(actors)
        gaps = _gaps(area_study, evidence)
        output = ActorNetworkScenarioOutput(actors=actors, relationships=relationships, evidence_gaps=gaps)
        local_citations = _local_citations(evidence)
        answer = _render_answer(output, evidence, area_study)
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[*citation_titles(S2_REFERENCES), *[citation.title for citation in local_citations]],
            structured_citations=[*structured_citations(S2_REFERENCES), *local_citations],
            source_trust=[*source_trust_markers(S2_REFERENCES), *_local_source_trust(context)],
            confidence=Confidence.low,
            follow_up_questions=[
                "Which organizations or institutions are confirmed by approved public or scenario sources?",
                "What relationship, influence, or friction point would change the planning decision?",
                "Which gap needs validation before treating this network as more than a planning hypothesis?",
            ],
            scenario_output=output.model_dump(),
            scenario_output_status=ScenarioOutputStatus.validated,
        )

    def _safety_response(self, input_text: str) -> AgentRunResponse:
        output = ActorNetworkScenarioOutput(
            evidence_gaps=["Individual targeting and private-person profiling are outside this advisory's scope."]
        )
        return self._response(
            answer=(
                "Actor Network Analyst — safe planning boundary\n\n"
                "I cannot map named civilians or support individual targeting. I can support a training-safe, "
                "organization-level map of public institutions, broad actor categories, and documented relationships.\n\n"
                "Evidence gaps:\n- Confirm an approved, public, local, training, or fictional scenario scope.\n\n"
                + _DRAFT_WARNING
            ),
            input_text=input_text,
            citations=citation_titles(S2_REFERENCES),
            structured_citations=structured_citations(S2_REFERENCES),
            source_trust=source_trust_markers(S2_REFERENCES),
            confidence=Confidence.low,
            scenario_output=output.model_dump(),
            scenario_output_status=ScenarioOutputStatus.validated,
            additional_warnings=["Sensitive request: individual targeting and private-person profiling are not supported."],
        )


def build_actor_network_agent() -> ActorNetworkAnalystAgent:
    return ActorNetworkAnalystAgent()


def _source_evidence(context: AgentContext) -> list[dict[str, str]]:
    raw = context.extra.get("source_evidence")
    return [{str(k): str(v) for k, v in item.items() if v is not None} for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []


def _assessment(context: AgentContext, role: str) -> dict[str, object]:
    value = context.prior_assessments.get(role)
    return value if isinstance(value, dict) else {}


def _actors_from_evidence(evidence: list[dict[str, str]]) -> list[dict[str, str]]:
    if not evidence:
        return [{"actor": "Organizations and institutions not yet supplied", "interest": "Collection gap", "influence": "Unknown", "confidence": "low"}]
    return [
        {
            "actor": item.get("publisher") or item.get("title", "Source-described organization"),
            "interest": "Interpret only from supplied public or scenario evidence.",
            "influence": "Not independently assessed.",
            "confidence": "low",
        }
        for item in evidence
    ]


def _relationships(actors: list[dict[str, str]]) -> list[dict[str, str]]:
    if len(actors) < 2:
        return [{"from": actors[0]["actor"], "to": "Other relevant institutions", "relationship": "Unknown; validate before use.", "confidence": "low"}]
    return [{"from": actors[0]["actor"], "to": actors[1]["actor"], "relationship": "Relationship not established by supplied evidence.", "confidence": "low"}]


def _gaps(area_study: dict[str, object], evidence: list[dict[str, str]]) -> list[str]:
    gaps = ["Validate organization interests, capabilities, and relationships with approved public or scenario sources."]
    if not area_study:
        gaps.append("No prior area-study handoff supplied; confirm operational-area and civil-context baseline.")
    else:
        area_gaps = area_study.get("evidence_gaps")
        if isinstance(area_gaps, list):
            for gap in area_gaps[:2]:
                if isinstance(gap, str) and gap.strip():
                    gaps.append(f"Inherited area-study gap: {gap}")
    if not evidence:
        gaps.append("No local evidence attached or retrieved; network remains a planning scaffold.")
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


def _render_answer(output: ActorNetworkScenarioOutput, evidence: list[dict[str, str]], area_study: dict[str, object]) -> str:
    actor_lines = "\n".join(f"- {item['actor']}: interest={item['interest']}; influence={item['influence']}; confidence={item['confidence']}." for item in output.actors)
    relationship_lines = "\n".join(f"- {item['from']} → {item['to']}: {item['relationship']} (confidence: {item['confidence']})." for item in output.relationships)
    evidence_lines = "\n".join(f"- {item.get('title', 'Saved local source')}: {item.get('excerpt', 'No excerpt supplied.')}" for item in evidence) or "- No local evidence was attached or retrieved."
    area_note = (
        f"Area-study handoff received for {area_study.get('operational_area', 'an unspecified planning area')}."
        if area_study
        else "No area-study handoff received; use this as a collection scaffold only."
    )
    return (
        "Actor Network Analyst — organization-level planning scaffold\n\n"
        f"Upstream context: {area_note}\n\nSource observations:\n{evidence_lines}\n\n"
        f"Actors (organizations and broad categories only):\n{actor_lines}\n\nRelationships:\n{relationship_lines}\n\n"
        "Evidence gaps:\n" + "\n".join(f"- {gap}" for gap in output.evidence_gaps) + "\n\n"
        "Handoff note: treat all unvalidated relationships as collection needs, not facts.\n\n" + _DRAFT_WARNING
    )
