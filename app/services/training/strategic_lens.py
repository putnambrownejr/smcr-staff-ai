"""Build bounded fictional or public-source strategic lenses for training."""

from __future__ import annotations

from collections.abc import Iterable

from app.schemas.strategic_lens import (
    StrategicLensEvidenceProvenance,
    StrategicLensMode,
    StrategicLensOutput,
    StrategicLensRequest,
    StrategicPostureCard,
)

_ASSUMPTION = "Scenario assumption: "

_CARD_CONTENT: dict[StrategicPostureCard, dict[str, str]] = {
    StrategicPostureCard.indirect_leverage: {
        "objective": "seek influence through indirect pressure rather than decisive confrontation",
        "advantage": "create decision friction by shaping conditions around a problem",
        "risk": "avoid commitments that remove room to adjust",
        "force": "favor dispersed, non-decisive exercise pressure",
        "information": "use ambiguity to complicate interpretation",
        "constraint": "depends on sustained ambiguity and credible alternatives",
        "indicator": "does the exercise actor repeatedly choose indirect pressure over a direct decision?",
    },
    StrategicPostureCard.legitimacy_first: {
        "objective": "preserve perceived legitimacy while pursuing the scenario objective",
        "advantage": "treat political acceptance as a source of resilience",
        "risk": "avoid visible actions that undermine support",
        "force": "favor pressure that can be framed as protective or responsive",
        "information": "prioritize narrative consistency and audience confidence",
        "constraint": "depends on maintaining credible public support",
        "indicator": "would the actor change course when legitimacy costs exceed exercise gains?",
    },
    StrategicPostureCard.threshold_sensitive: {
        "objective": "advance objectives while remaining below a scenario escalation threshold",
        "advantage": "sequence pressure gradually to preserve options",
        "risk": "calibrate activity to avoid triggering a stronger response",
        "force": "favor reversible, paced exercise moves",
        "information": "signal restraint while preserving uncertainty",
        "constraint": "depends on a shared understanding of relevant thresholds",
        "indicator": "does pressure pause or change after threshold cues appear?",
    },
    StrategicPostureCard.systems_friction: {
        "objective": "delay or complicate coordinated decision-making in the exercise",
        "advantage": "gain time by increasing cross-organizational friction",
        "risk": "accept slow progress if it preserves decision advantage",
        "force": "emphasize broad coordination pressure, not tactical action",
        "information": "introduce competing narratives and administrative uncertainty",
        "constraint": "depends on existing seams between organizations or processes",
        "indicator": "do decisions slow when coordination demands increase?",
    },
    StrategicPostureCard.information_contest: {
        "objective": "shape how relevant audiences interpret the exercise situation",
        "advantage": "make narrative and confidence part of the decision environment",
        "risk": "avoid claims that can be readily disproved in the scenario",
        "force": "use force-related activity only as high-level context",
        "information": "prioritize competing accounts, ambiguity, and credibility contests",
        "constraint": "depends on audience access and narrative credibility",
        "indicator": "do audience perceptions diverge despite the same exercise facts?",
    },
    StrategicPostureCard.partner_reliance: {
        "objective": "pursue objectives through partners and influence networks",
        "advantage": "distribute burden and preserve distance from outcomes",
        "risk": "limit exposure by retaining plausible separation from partners",
        "force": "favor partner-enabled exercise pressure",
        "information": "reinforce partner narratives and shared interests",
        "constraint": "depends on partner alignment and reliability",
        "indicator": "would the scenario posture weaken if a partner withheld support?",
    },
    StrategicPostureCard.short_term_risk: {
        "objective": "seek a near-term political or decision advantage despite uncertainty",
        "advantage": "accept temporary costs to alter the exercise timeline",
        "risk": "tolerate bounded short-term setbacks for perceived larger gain",
        "force": "favor time-sensitive, high-level exercise pressure",
        "information": "emphasize urgency and fait-accompli framing",
        "constraint": "depends on a credible path from short-term cost to longer-term gain",
        "indicator": "does the actor persist after a bounded setback to preserve timing?",
    },
    StrategicPostureCard.force_preservation: {
        "objective": "preserve future options and avoid a decisive exercise commitment",
        "advantage": "retain capacity and flexibility over immediate gain",
        "risk": "avoid attrition or commitment that forecloses later choices",
        "force": "favor delay, dispersion, and withdrawal in high-level scenario framing",
        "information": "frame restraint as deliberate rather than passive",
        "constraint": "depends on time and space to defer commitment",
        "indicator": "does the actor avoid commitment when costs become difficult to reverse?",
    },
    StrategicPostureCard.asymmetric_systems_effect: {
        "objective": "seek a disproportionate exercise effect through a perceived asymmetry",
        "advantage": "focus on decision-level effects instead of matching strength directly",
        "risk": "test assumptions before depending on a single asymmetric advantage",
        "force": "represent broad system-level pressure without targets or exploit paths",
        "information": "emphasize uncertainty about which systems or relationships matter most",
        "constraint": "depends on the asymmetry being real and durable",
        "indicator": "does the assumed asymmetry still matter after counter-pressure is applied?",
    },
}


class StrategicLensBuilder:
    """Normalize strategic patterns without inferring real-world conduct or intent."""

    def build(self, request: StrategicLensRequest, evidence: list[dict[str, str]]) -> StrategicLensOutput:
        if request.mode is StrategicLensMode.fictional:
            return self._build_fictional(request)
        return self._build_public_source(request, evidence)

    def _build_fictional(self, request: StrategicLensRequest) -> StrategicLensOutput:
        if not request.fictional_actor_confirmed:
            raise ValueError("Fictional strategic lenses require confirmation that the actor is fictional.")
        cards = _distinct_cards(request.posture_cards)
        if not 2 <= len(cards) <= 4:
            raise ValueError("Fictional strategic lenses require two to four distinct posture cards.")
        content = [_CARD_CONTENT[card] for card in cards]
        return StrategicLensOutput(
            mode=request.mode,
            actor_name=request.actor_name,
            strategic_objective=_assumptions(content, "objective"),
            theory_of_advantage=_assumptions(content, "advantage"),
            risk_and_escalation_posture=_assumptions(content, "risk"),
            force_employment_preference=_assumptions(content, "force"),
            information_posture=_assumptions(content, "information"),
            constraints=_assumptions(content, "constraint"),
            observable_indicators=_assumptions(content, "indicator"),
            competing_interpretation=(
                _ASSUMPTION + "the actor may be responding to routine exercise constraints rather than a coherent posture."
            ),
            discriminator=(
                _ASSUMPTION + "test whether the actor changes its approach when the stated counter-pressure removes its assumed advantage."
            ),
            hypotheses=[_ASSUMPTION + f"{request.actor_name} is represented through selected posture cards, not as a real-world forecast."],
            evidence_gaps=["Scenario design should test each selected posture card before treating it as an enduring exercise condition."],
        )

    def _build_public_source(self, request: StrategicLensRequest, evidence: list[dict[str, str]]) -> StrategicLensOutput:
        reviewed = _reviewed_evidence(evidence)
        if not reviewed:
            raise ValueError("Public-source strategic lenses require reviewed local evidence with source hashes.")
        observations = [
            f"Attributed observation — {item['title']} ({item['source_hash']}): {item['excerpt']}"
            for item in reviewed
        ]
        provenance = [
            StrategicLensEvidenceProvenance(
                title=item["title"],
                url=item["url"] or None,
                publisher=item["publisher"] or None,
                retrieved_at=item["retrieved_at"] or None,
                source_hash=item["source_hash"],
                trust_status=item["trust_status"],
            )
            for item in reviewed
        ]
        hashes = list(dict.fromkeys(item["source_hash"] for item in reviewed))
        return StrategicLensOutput(
            mode=request.mode,
            actor_name=request.actor_name,
            competing_interpretation=(
                "Competing interpretation: the cited observations may reflect temporary conditions, institutional process, "
                "or source framing rather than a stable strategic preference."
            ),
            discriminator=(
                "Discriminator: additional reviewed local evidence that shows whether the same observation persists "
                "across context and time would change this assessment."
            ),
            evidence_observations=observations,
            evidence_provenance=provenance,
            source_hashes=hashes,
            hypotheses=[
                "Hypothesis: assess whether the attributed observations support a coherent strategic lens; they do not predict intent or conduct."
            ],
            evidence_gaps=[
                "No conclusion beyond the attributed excerpts is supported without additional reviewed local evidence.",
                "Confirm source scope, date, and trust status before using this lens in a planning product.",
            ],
        )


def _distinct_cards(cards: Iterable[StrategicPostureCard]) -> list[StrategicPostureCard]:
    return list(dict.fromkeys(cards))


def _assumptions(content: list[dict[str, str]], key: str) -> list[str]:
    return [_ASSUMPTION + card[key] for card in content]


def _reviewed_evidence(evidence: list[dict[str, str]]) -> list[dict[str, str]]:
    reviewed: list[dict[str, str]] = []
    for item in evidence:
        title = item.get("title", "").strip()
        excerpt = item.get("excerpt", "").strip()
        source_hash = item.get("source_hash", "").strip()
        if item.get("trust_status") == "current" and title and excerpt and source_hash:
            reviewed.append(
                {
                    "title": title,
                    "excerpt": excerpt,
                    "source_hash": source_hash,
                    "url": item.get("url", "").strip(),
                    "publisher": item.get("publisher", "").strip(),
                    "retrieved_at": item.get("retrieved_at", "").strip(),
                    "trust_status": item["trust_status"],
                }
            )
    return reviewed
