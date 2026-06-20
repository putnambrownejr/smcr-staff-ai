from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input, should_limit_to_generic_response
from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.schemas.user_context import ActiveUserContext


class AgentContext(BaseModel):
    user_key: str | None = None
    user_role: str | None = None
    unit_id: str | None = None
    request_is_training_or_fictional: bool = False
    extra: dict[str, object] = Field(default_factory=dict)


class Agent(ABC):
    metadata: AgentMetadata

    @abstractmethod
    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        raise NotImplementedError

    def _response(
        self,
        answer: str,
        input_text: str,
        follow_up_questions: list[str] | None = None,
        citations: list[str] | None = None,
        structured_citations: list[StructuredCitation] | None = None,
        source_trust: list[SourceTrustMarker] | None = None,
        confidence: Confidence = Confidence.low,
    ) -> AgentRunResponse:
        warnings = [*DEFAULT_WARNINGS, *detect_sensitive_input(input_text)]
        if should_limit_to_generic_response(input_text):
            answer = (
                "I cannot process classified, controlled, COMSEC, keying material, real frequencies, "
                "call signs, exact movements, or sensitive operational details. "
                "Here is a generic training-only checklist instead:\n\n"
                f"{answer}"
            )
            confidence = Confidence.low
        return AgentRunResponse(
            agent_id=self.metadata.id,
            answer=answer,
            citations=citations or [],
            structured_citations=structured_citations or [],
            source_trust=source_trust or _default_source_trust(self.metadata),
            warnings=warnings,
            human_review_required=self.metadata.required_human_review,
            confidence=confidence,
            follow_up_questions=follow_up_questions or [],
        )

    def _active_context_lines(self, context: AgentContext) -> list[str]:
        active_context = _active_context_from_context(context)
        if active_context is None:
            return []
        lines: list[str] = []
        if active_context.unit_name or active_context.unit_type or active_context.unit_family:
            unit_bits = [
                item
                for item in [
                    active_context.unit_name,
                    active_context.unit_type,
                    active_context.unit_family,
                ]
                if item
            ]
            lines.append("Active local context: " + " / ".join(unit_bits))
        if active_context.billet_override:
            lines.append(f"Billet emphasis: {active_context.billet_override}")
        if active_context.mos_override:
            lines.append(f"MOS emphasis: {active_context.mos_override}")
        lines.extend(f"Current focus: {item}" for item in active_context.current_focus[:3])
        lines.extend(f"Staff bias: {item}" for item in active_context.staff_bias[:3])
        lines.extend(f"Temporary note: {item}" for item in active_context.temporary_notes[:2])
        lines.extend(_unit_bias_lines(active_context))
        return lines


class PlaceholderAgent(Agent):
    def __init__(
        self,
        metadata: AgentMetadata,
        checklist: list[str],
        follow_up_questions: list[str] | None = None,
    ) -> None:
        self.metadata = metadata
        self.checklist = checklist
        self.default_follow_up_questions = follow_up_questions or [
            "What public source or doctrine should this draft be grounded in?",
            "Is this for a fictional/training scenario or a real-world administrative workflow?",
        ]

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        lines = "\n".join(f"- {item}" for item in self.checklist)
        answer = (
            f"[{self.metadata.name} — no LLM connected. "
            "Paste this into your AI assistant to get a real response. "
            "The checklist below is structured context for that conversation, "
            "not AI-generated output.]\n\n"
            f"Checklist items:\n{lines}"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            follow_up_questions=self.default_follow_up_questions,
        )


def _default_source_trust(metadata: AgentMetadata) -> list[SourceTrustMarker]:
    if not metadata.citation_required:
        return []
    return [
        SourceTrustMarker(
            tracked_title=source,
            status=VerifiedSourceStatus.needs_review,
            notes="Review this source against the latest verified public reference before acting.",
        )
        for source in metadata.allowed_sources[:3]
    ]


def _active_context_from_context(context: AgentContext) -> ActiveUserContext | None:
    raw = context.extra.get("active_user_context")
    if not isinstance(raw, dict):
        return None
    try:
        return ActiveUserContext.model_validate(raw)
    except Exception:
        return None


def _unit_bias_lines(active_context: ActiveUserContext) -> list[str]:
    searchable = " ".join(
        [
            active_context.unit_name or "",
            active_context.unit_type or "",
            active_context.unit_family or "",
            active_context.billet_override or "",
            active_context.mos_override or "",
            *active_context.current_focus,
            *active_context.staff_bias,
            *active_context.temporary_notes,
        ]
    ).lower()
    lines: list[str] = []
    if any(token in searchable for token in ("civil affairs", "civil-affairs", "ca team", "0520", "0530")):
        lines.append("Bias the advice toward civil reconnaissance, partner continuity, and public-source context.")
    if any(token in searchable for token in ("comm", "communications", "0602", "0631", "network", "radio")):
        lines.append(
            "Bias the advice toward information flow, PACE realism, permissions, access, "
            "and operator rehearsal."
        )
    if any(token in searchable for token in ("wing", "aviation", "air", "sortie", "maintenance")):
        lines.append(
            "Bias the advice toward aviation supportability, sequencing, maintenance rhythm, "
            "and air-ground coordination."
        )
    if any(token in searchable for token in ("infantry", "03", "rifle", "weapons", "maneuver")):
        lines.append(
            "Bias the advice toward field execution, maneuver standards, live-fire safety, "
            "and small-unit fundamentals."
        )
    return lines
