"""Virtual staff round table — concurrent multi-agent scenario assessment.

Execution model:

1. **Opening assessments** — every participant runs concurrently against the
   scenario with no shared context, producing independent perspectives.
2. **Cross-review** (optional, and only when the opening round produced
   structured assessments) — every participant re-runs concurrently, this
   time seeing every *other* participant's structured assessment via
   ``AgentContext.prior_assessments``.
3. **Synthesis** — a synthesizer agent (Chief of Staff by default) runs last
   with the full set of final assessments and produces the integrated
   command-team picture.

In local template mode (no external LLM configured) no structured
assessments exist, so the cross-review round is skipped with a warning and
the round table degrades to a parallel staff council plus synthesis.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from app.schemas.agents import AgentRunResponse
from app.schemas.roundtable import (
    RoundtableEntry,
    RoundtableRequest,
    RoundtableResponse,
    RoundtableRound,
)
from app.services.agents.base import Agent, AgentContext
from app.services.agents.perspective import apply_external_perspective

ContextFactory = Callable[[dict[str, object]], AgentContext]

_MAX_WORKERS = 8

# Participants included in every auto-selected round table. The XO sits at
# every table as the staff integrator; S-2 and the planning advisor frame the
# problem.
CORE_PARTICIPANTS: tuple[str, ...] = ("staff-xo", "staff-s2", "planning-advisor")

# Every staff seat plus the cross-cutting advisors — the "whole staff answers
# in one go" preset for generic questions and training help.
FULL_STAFF_PARTICIPANTS: tuple[str, ...] = (
    "staff-xo",
    "staff-opso",
    "staff-s1",
    "staff-s2",
    "staff-s4",
    "staff-s6",
    "staff-sel",
    "staff-surgeon",
    "staff-sja",
    "staff-pao",
    "staff-chaplain",
    "staff-provost",
    "staff-ig",
    "staff-g8",
    "staff-g9",
    "staff-battle_captain",
    "planning-advisor",
    "orm-risk-management",
    "red-team-assumptions-challenge",
)

# The seats that build and run a drill weekend, range day, or exercise.
TRAINING_PARTICIPANTS: tuple[str, ...] = (
    "staff-opso",
    "staff-xo",
    "staff-s1",
    "staff-s4",
    "staff-s6",
    "staff-sel",
    "staff-surgeon",
    "staff-sja",
    "orm-risk-management",
    "assessment-learning-advisor",
    "planning-advisor",
)

# The commander's inner circle for a personnel, climate, or decision question.
COMMAND_TEAM_PARTICIPANTS: tuple[str, ...] = (
    "staff-xo",
    "staff-opso",
    "staff-sel",
    "staff-s1",
    "staff-sja",
    "staff-chaplain",
    "planning-advisor",
    "red-team-assumptions-challenge",
)

PRESET_PARTICIPANTS: dict[str, tuple[str, ...]] = {
    "full_staff": FULL_STAFF_PARTICIPANTS,
    "training": TRAINING_PARTICIPANTS,
    "command_team": COMMAND_TEAM_PARTICIPANTS,
}

# Scenario keywords that pull additional staff sections to the table.
AGENT_TRIGGERS: dict[str, tuple[str, ...]] = {
    "staff-opso": (
        "training", "drill weekend", "range", "exercise", "annual training", "field",
        "rehearsal", "t&r", "metl", "live-fire", "live fire", "stx", "ftx",
    ),
    "orm-risk-management": (
        "training", "range", "exercise", "live-fire", "live fire", "safety", "risk",
        "hazard", "orm", "pt ", "physical training", "movement",
    ),
    "assessment-learning-advisor": ("aar", "after action", "lessons learned", "metl", "t&r", "assessment"),
    "staff-s1": ("fitrep", "orders", "mrows", "dts", "pay", "admin", "award", "personnel", "roster"),
    "staff-sel": ("discipline", "standards", "ceremony", "promotion", "pme", "enlisted", "morale"),
    "staff-g9": (
        "humanitarian", "disaster", "civil", "population", "displaced", "refugee",
        "ngo", "embassy", "host nation", "partner nation", "evacuation",
        "earthquake", "hurricane", "typhoon", "flood", "tsunami", "wildfire",
    ),
    "staff-s4": (
        "logistic", "supply", "port", "airport", "airfield", "transport",
        "movement", "fuel", "sustainment", "embark", "lift", "convoy",
        # LCE-flavored tasks route to the S-4 seat (the LCE lane merged into it)
        "lce", "mlg", "clb", "combat logistics", "distribution", "class viii",
        "reconstitution", "health service",
    ),
    "ace": (
        "aviation", "air support", "airspace", "sortie", "helicopter", "osprey",
        "assault support", "cas ", "airlift",
    ),
    "gce": (
        "maneuver", "infantry", "ground assault", "raid", "security force",
        "scheme of maneuver", "rifle company",
    ),
    "staff-s6": (
        "comm", "network", "radio", "satcom", "pace plan", "spectrum",
        "cyber", "bandwidth",
    ),
    "staff-surgeon": (
        "casualt", "medical", "medevac", "casevac", "disease", "injur",
        "hospital", "epidemic", "cholera",
    ),
    "staff-sja": (
        "legal", "roe", "ruf", "sofa", "detainee", "claims", "posse comitatus",
    ),
    "staff-pao": (
        "media", "press", "public affairs", "narrative", "messaging",
        "social media",
    ),
    "staff-provost": (
        "access control", "force protection", "crowd", "riot", "perimeter",
    ),
    "staff-g8": (
        "funding", "budget", "cost", "fiscal",
    ),
}


class UnknownRoundtableAgentError(ValueError):
    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Unknown agent in round table: {agent_id}")
        self.agent_id = agent_id


def resolve_participants(
    scenario: str,
    requested: list[str],
    synthesizer: str | None,
    preset: str = "auto",
) -> tuple[list[str], list[str]]:
    """Return (participants, auto_selected). The synthesizer never sits as a participant.

    Explicit ``requested`` ids always win. Otherwise a named preset seats a
    fixed council; ``auto`` seats the core plus whatever the scenario text
    triggers, and falls back to the full staff when nothing specific is
    triggered so a generic question still gets every section's view.
    """
    if requested:
        participants = [agent_id for agent_id in dict.fromkeys(requested) if agent_id != synthesizer]
        return participants, []
    if preset in PRESET_PARTICIPANTS:
        participants = [agent_id for agent_id in PRESET_PARTICIPANTS[preset] if agent_id != synthesizer]
        return participants, list(participants)
    lowered = scenario.lower()
    auto = [
        agent_id
        for agent_id, triggers in AGENT_TRIGGERS.items()
        if any(trigger in lowered for trigger in triggers)
    ]
    if not auto:
        participants = [agent_id for agent_id in FULL_STAFF_PARTICIPANTS if agent_id != synthesizer]
        return participants, list(participants)
    participants = [
        *(agent_id for agent_id in CORE_PARTICIPANTS if agent_id != synthesizer),
        *(agent_id for agent_id in auto if agent_id not in CORE_PARTICIPANTS and agent_id != synthesizer),
    ]
    return participants, auto


class RoundtableService:
    def __init__(self, agents: dict[str, Agent]) -> None:
        """``agents`` must contain every participant plus the synthesizer, pre-validated."""
        self._agents = agents

    def run(
        self,
        request: RoundtableRequest,
        context_factory: ContextFactory,
        participants: list[str],
        auto_selected: list[str],
        *,
        preview_only: bool = False,
    ) -> RoundtableResponse:
        warnings: list[str] = []
        rounds_out: list[RoundtableRound] = []

        # Round 1 — independent opening assessments, run concurrently.
        opening = self._run_round(
            participants,
            request.scenario,
            context_factory,
            prior_for=lambda _agent_id: {},
            preview_only=preview_only,
        )
        rounds_out.append(RoundtableRound(name="opening_assessments", entries=opening))
        assessments = _collect_assessments(opening)
        own_role = {
            entry.agent_id: str(entry.scenario_output.get("role"))
            for entry in opening
            if entry.scenario_output is not None
        }

        # Round 2 — cross-review with everyone else's assessment on the table.
        if request.rounds >= 2 and assessments:
            def prior_for(agent_id: str) -> dict[str, object]:
                own = own_role.get(agent_id)
                return {role: output for role, output in assessments.items() if role != own}

            cross_review = self._run_round(
                participants,
                request.scenario,
                context_factory,
                prior_for=prior_for,
                preview_only=preview_only,
            )
            rounds_out.append(RoundtableRound(name="cross_review", entries=cross_review))
            assessments.update(_collect_assessments(cross_review))
        elif request.rounds >= 2:
            warnings.append(
                "Cross-review round skipped: the opening round produced no structured assessments "
                "(local template mode). Each entry below is an independent, fixed template."
            )

        # Synthesis — one agent integrates the final picture (external AI only;
        # in local mode this is the synthesizer's own template, labelled as such).
        synthesis_entry: RoundtableEntry | None = None
        if request.synthesizer:
            synth_context = context_factory(dict(assessments))
            synth_agent = self._agents[request.synthesizer]
            synth_response = synth_agent.run(request.scenario, synth_context)
            synth_response = apply_external_perspective(
                synth_agent, synth_response, request.scenario, synth_context, synthesis=True
            )
            synthesis_entry = _entry(request.synthesizer, synth_response)
            warnings.extend(synth_response.warnings)
            if synth_response.scenario_output is not None:
                role_key = str(synth_response.scenario_output.get("role", request.synthesizer))
                assessments[role_key] = synth_response.scenario_output

        for round_result in rounds_out:
            for entry in round_result.entries:
                warnings.extend(entry.warnings)
                if entry.scenario_output_status == "invalid":
                    warnings.append(
                        f"{entry.agent_id} did not produce a valid structured assessment; "
                        "its perspective is text-only."
                    )

        external = any(
            entry.scenario_output_status in {"validated", "invalid"}
            for round_result in rounds_out
            for entry in round_result.entries
        )
        if not external:
            warnings.insert(
                0,
                "NO AI ANALYSIS WAS PERFORMED. No external AI is configured (or local-only was chosen), so every "
                "entry below is that seat's fixed doctrine template — the questions it always asks — organized "
                "for you. Use POST /agents/roundtable/packet (or the dashboard's 'Build staff call packet') to "
                "hand this to your own AI, or configure LLM_API_KEY for a live round table.",
            )
        return RoundtableResponse(
            scenario=request.scenario,
            mode="external_ai" if external else "local_templates",
            participants=participants,
            auto_selected=auto_selected,
            rounds=rounds_out,
            synthesis=synthesis_entry,
            assessments=assessments,
            warnings=list(dict.fromkeys(warnings)),
        )

    def _run_round(
        self,
        participants: list[str],
        scenario: str,
        context_factory: ContextFactory,
        prior_for: Callable[[str], dict[str, object]],
        preview_only: bool,
    ) -> list[RoundtableEntry]:
        def call(agent_id: str) -> RoundtableEntry:
            context = context_factory(prior_for(agent_id))
            agent = self._agents[agent_id]
            response = apply_external_perspective(agent, agent.run(scenario, context), scenario, context)
            return _entry(agent_id, response)

        # Preview mode runs sequentially so the first outbound preview surfaces
        # deterministically instead of racing across threads.
        if preview_only or len(participants) == 1:
            return [call(agent_id) for agent_id in participants]
        with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(participants))) as pool:
            futures = [pool.submit(call, agent_id) for agent_id in participants]
            return [future.result() for future in futures]


def _entry(agent_id: str, response: AgentRunResponse) -> RoundtableEntry:
    return RoundtableEntry(
        agent_id=agent_id,
        answer=response.answer,
        scenario_output=response.scenario_output,
        scenario_output_status=response.scenario_output_status.value,
        confidence=response.confidence.value,
        follow_up_questions=response.follow_up_questions,
        warnings=response.warnings,
    )


def _collect_assessments(entries: list[RoundtableEntry]) -> dict[str, object]:
    assessments: dict[str, object] = {}
    for entry in entries:
        if entry.scenario_output is not None:
            role_key = str(entry.scenario_output.get("role", entry.agent_id))
            assessments[role_key] = entry.scenario_output
    return assessments
