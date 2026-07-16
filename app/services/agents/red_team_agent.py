from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.civil_network import CivilNetworkSnapshot
from app.schemas.source_state import SourceTrustMarker
from app.schemas.strategic_lens import StrategicLensMode, StrategicLensOutput, StrategicLensRequest
from app.schemas.training import ScenarioArchetype
from app.services.agents.base import Agent, AgentContext
from app.services.agents.civil_network_context import (
    civil_network_sections,
    civil_network_snapshot,
    civil_network_source_trust,
)
from app.services.agents.source_refs import (
    S2_REFERENCES,
    S3_REFERENCES,
    STAFF_PROCESS_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)
from app.services.training.redcell_engine import build_redcell_design
from app.services.training.scenario_engine import infer_archetype_from_text
from app.services.training.strategic_lens import StrategicLensBuilder

_DRAFT_WARNING = "DRAFT — Verify all references against current official sources before acting."
_MODES = {"assumptions", "evidence", "hypotheses"}


class RedTeamAssumptionsAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="red-team-assumptions-challenge",
            name="Red Team / Assumptions Challenge",
            description=(
                "Pressures staff logic, weak assumptions, fake COA differences, and polite groupthink before a plan "
                "hardens into an avoidable problem."
            ),
            domain="critical challenge",
            intended_users=["SMCR officers", "XO", "S-3", "planning teams", "command teams"],
            allowed_sources=[
                "public planning doctrine",
                "public command and staff PME references",
                "local training-only staff products",
            ],
            disallowed_inputs=[
                "classified operational details",
                "real-world targeting or sensitive movement details",
            ],
            system_prompt=(
                "Respond like a disciplined red-team officer working under a hard S-3. Be constructive, "
                "unsentimental, and specific. Challenge assumptions, false certainty, and cosmetic alternatives "
                "without becoming theatrical."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        snapshot = civil_network_snapshot(context)
        mode = _mode(context)
        strategic_lens = _strategic_lens(context)
        if mode == "evidence":
            return self._with_civil_network(self._evidence_response(input_text, context, strategic_lens), snapshot)
        if mode == "hypotheses":
            return self._with_civil_network(self._hypotheses_response(input_text, context, strategic_lens), snapshot)
        return self._with_civil_network(self._assumptions_response(input_text, context, strategic_lens), snapshot)

    def _with_civil_network(
        self, response: AgentRunResponse, snapshot: CivilNetworkSnapshot | None
    ) -> AgentRunResponse:
        if snapshot is None:
            return response
        response.answer = (
            response.answer.removesuffix(_DRAFT_WARNING) + civil_network_sections(snapshot) + _DRAFT_WARNING
        )
        response.source_trust.extend(civil_network_source_trust(snapshot))
        return response

    def _assumptions_response(
        self, input_text: str, context: AgentContext, strategic_lens: StrategicLensOutput | None
    ) -> AgentRunResponse:
        archetype = _infer_archetype(input_text)
        redcell = build_redcell_design(
            archetype=archetype,
            actor_name="fictional adversary cell",
            place_name="the training area",
        )
        stereotype_lines = "\n".join(
            (
                f"- {item.label}: {item.summary}\n"
                f"  - indicators: {', '.join(item.indicators[:2])}\n"
                f"  - preferred seams: {', '.join(item.preferred_seams[:2])}\n"
                f"  - likely friendly mistakes: {', '.join(item.likely_friendly_mistakes[:2])}"
            )
            for item in redcell.stereotypes
        )
        question_lines = "\n".join(f"- {item}" for item in redcell.questions[:5])
        answer = (
            "Red-team / assumptions challenge advisory.\n\n"
            "Use this before the staff falls in love with its own draft.\n\n"
            f"Threat pattern read: `{archetype.value}`\n\n"
            "What to challenge:\n"
            "- Which assumption is carrying the most weight with the least evidence?\n"
            "- Which part of the concept fails first under friction?\n"
            "- Which adjacent section dependency is being treated like a given?\n"
            "- Are the COAs real alternatives or just wording changes?\n"
            "- What is the enemy, environment, or civil factor the staff is quietly hand-waving?\n\n"
            "Threat actor stereotype board:\n"
            f"{stereotype_lines}\n\n"
            "Red-team pattern:\n"
            "- Name the claim.\n"
            "- State why it may be weak.\n"
            "- Identify what would prove it wrong.\n"
            "- Recommend the smallest useful correction.\n\n"
            "Red-cell questions:\n"
            f"{question_lines}\n\n"
            f"{_assumptions_lens_section(strategic_lens)}"
            "Helpful red-cell cuts:\n"
            "- If the adversary is probing, what routine are we showing it?\n"
            "- If the adversary wants overreaction, where are we easiest to bait?\n"
            "- If the adversary wants delay, which support or reporting seam buys it time fastest?\n"
            "- If the adversary wants confusion, what rumor or partial truth would the staff believe too quickly?\n\n"
            "Watch for soft failures:\n"
            "- Everyone agrees too quickly.\n"
            "- The plan depends on support that has not actually been confirmed.\n"
            "- Risk language exists, but nobody can say what would trigger a branch or abort.\n"
            "- The brief sounds polished because the hard part was edited out.\n"
            f"\n{_DRAFT_WARNING}"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
            structured_citations=structured_citations((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
            source_trust=source_trust_markers(
                (*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES),
                notes_prefix=(
                    "Verify current planning and staff references before presenting this as a formal critique."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What assumption would most change the plan if it proved wrong?",
                "Which threat actor stereotype best fits the scenario, and what seam would that actor hit first?",
                "Which COA difference is currently more cosmetic than real?",
                "What failure trigger should the staff state explicitly?",
            ],
        )

    def _evidence_response(
        self, input_text: str, context: AgentContext, strategic_lens: StrategicLensOutput | None
    ) -> AgentRunResponse:
        evidence = _source_evidence(context)
        local_citations = _local_citations(evidence)
        if evidence:
            ledger = "\n".join(
                (
                    f"- Claim: {item.get('excerpt', 'No excerpt supplied.')}\n"
                    f"  - Source: {item.get('title', 'Saved local source')} "
                    f"(chunk {item.get('chunk_id', 'unknown')}; trust: {item.get('trust_status', 'unknown')})\n"
                    "  - Assessment: supplied evidence only; corroboration and applicability require human review.\n"
                    "  - Collection need: seek an independent, current source before treating this as a planning fact."
                )
                for item in evidence
            )
        else:
            ledger = (
                "- Collection need: no saved local evidence was attached or retrieved.\n"
                "  - Do not promote the request text into a claim. Identify the decision, then collect approved public "
                "or scenario evidence that could support or refute it."
            )
        answer = (
            "Red-team / evidence advisory.\n\n"
            "Claim ledger:\n"
            f"{ledger}\n\n"
            "Review gate:\n"
            "- Separate source observations from staff assumptions.\n"
            "- Record corroboration, recency, and relevance before relying on any claim.\n"
            "- Convert unresolved claims into explicit collection needs.\n\n"
            f"{_evidence_lens_section(strategic_lens)}"
            f"{_DRAFT_WARNING}"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                *citation_titles((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
                *[citation.title for citation in local_citations],
            ],
            structured_citations=[
                *structured_citations((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
                *local_citations,
            ],
            source_trust=[
                *source_trust_markers((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
                *_local_source_trust(context),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Which claim has enough current, corroborated evidence to retain?",
                "Which collection need matters most to the next commander decision?",
            ],
        )

    def _hypotheses_response(
        self, input_text: str, context: AgentContext, strategic_lens: StrategicLensOutput | None
    ) -> AgentRunResponse:
        evidence = _source_evidence(context)
        local_citations = _local_citations(evidence)
        evidence_note = (
            "; ".join(item.get("title", "Saved local source") for item in evidence)
            if evidence
            else "No saved local evidence attached; these remain collection scaffolds."
        )
        answer = (
            "Red-team / hypotheses advisory.\n\n"
            "Competing hypotheses:\n"
            "- H1 — The current concept is feasible if stated dependencies hold.\n"
            "  - Support/refutation: validate each dependency with current, corroborated evidence.\n"
            "  - Discriminator: confirmed support, access, and timing against the stated conditions.\n"
            "- H2 — The concept fails because one or more dependencies are unavailable, late, or misread.\n"
            "  - Support/refutation: look for unconfirmed assumptions, conflicting source observations, or missing owners.\n"
            "  - Discriminator: a verified gap that changes the decision, branch, or abort trigger.\n\n"
            f"Evidence available: {evidence_note}\n\n"
            f"{_hypotheses_lens_section(strategic_lens)}"
            "Confidence: low until a human reviewer compares current evidence against the discriminators.\n"
            "What would change the assessment: confirmed or refuted evidence for the highest-consequence dependency.\n\n"
            f"{_DRAFT_WARNING}"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                *citation_titles((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
                *[citation.title for citation in local_citations],
            ],
            structured_citations=[
                *structured_citations((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
                *local_citations,
            ],
            source_trust=[
                *source_trust_markers((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
                *_local_source_trust(context),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Which discriminator can the staff validate before the next decision?",
                "What evidence would make you reject the current leading hypothesis?",
            ],
        )


def build_red_team_agent() -> RedTeamAssumptionsAgent:
    return RedTeamAssumptionsAgent()


def _infer_archetype(input_text: str) -> ScenarioArchetype:
    return infer_archetype_from_text(input_text)


def _mode(context: AgentContext) -> str:
    options = context.extra.get("agent_options")
    mode = options.get("mode", "assumptions") if isinstance(options, dict) else "assumptions"
    if not isinstance(mode, str) or mode not in _MODES:
        raise ValueError("Unsupported Red Team mode. Use assumptions, evidence, or hypotheses.")
    return mode


def _source_evidence(context: AgentContext) -> list[dict[str, str]]:
    raw = context.extra.get("source_evidence")
    if not isinstance(raw, list):
        return []
    return [
        {str(key): str(value) for key, value in item.items() if value is not None}
        for item in raw
        if isinstance(item, dict)
    ]


def _strategic_lens(context: AgentContext) -> StrategicLensOutput | None:
    options = context.extra.get("agent_options")
    raw = options.get("strategic_lens") if isinstance(options, dict) else None
    if raw is None:
        return None
    request = StrategicLensRequest.model_validate(raw)
    return StrategicLensBuilder().build(request, _source_evidence(context))


def _assumptions_lens_section(lens: StrategicLensOutput | None) -> str:
    if lens is None:
        return ""
    questions = "\n".join(
        f"- Mirror-imaging check: are we assuming {lens.actor_name} will share our framing of {item.removeprefix('Scenario assumption: ')}?"
        for item in lens.strategic_objective[:2]
    )
    return (
        "Strategic lens (exercise framing, not a forecast):\n"
        f"- Actor: {lens.actor_name}\n"
        f"{questions}\n"
        f"- Competing interpretation: {lens.competing_interpretation}\n"
        f"- Discriminator: {lens.discriminator}\n\n"
    )


def _evidence_lens_section(lens: StrategicLensOutput | None) -> str:
    if lens is None:
        return ""
    if lens.mode is StrategicLensMode.public_source:
        observations = "\n".join(f"- Observation: {item}" for item in lens.evidence_observations)
        provenance = "\n".join(
            f"- Source: {item.title} (hash: {item.source_hash}; trust: {item.trust_status}; retrieved: {item.retrieved_at or 'unknown'})"
            for item in lens.evidence_provenance
        )
        assumptions = "\n".join(f"- Hypothesis, not fact: {item}" for item in lens.hypotheses)
        return (
            "Strategic lens evidence (attributed local sources; not a forecast):\n"
            f"- Actor: {lens.actor_name}\n{observations}\n{provenance}\n{assumptions}\n\n"
        )
    assumptions = "\n".join(f"- Scenario assumption: {item}" for item in lens.hypotheses)
    return (
        "Strategic lens assumptions (fictional exercise framing, not evidence):\n"
        f"- Actor: {lens.actor_name}\n{assumptions}\n\n"
    )


def _hypotheses_lens_section(lens: StrategicLensOutput | None) -> str:
    if lens is None:
        return ""
    hypotheses = "\n".join(f"- {item}" for item in lens.hypotheses)
    observations = "\n".join(f"- Evidence: {item}" for item in lens.evidence_observations)
    return (
        "Strategic lens (exercise framing, not a forecast of real-world conduct):\n"
        f"- Actor: {lens.actor_name}\n"
        f"{observations + chr(10) if observations else ''}"
        f"Hypotheses:\n{hypotheses}\n"
        f"Competing interpretation: {lens.competing_interpretation}\n"
        f"Discriminator: {lens.discriminator}\n\n"
    )


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
        try:
            markers.append(item if isinstance(item, SourceTrustMarker) else SourceTrustMarker.model_validate(item))
        except ValueError:
            continue
    return markers
