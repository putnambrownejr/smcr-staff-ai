from __future__ import annotations

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.schemas.scenario_handoff import CoSScenarioOutput
from app.services.agents.base import Agent, AgentContext
from app.services.agents.reserve_admin_text import (
    NAVY_RESERVE_ADMIN,
    RESERVE_ADMIN_SYSTEMS,
    RESERVE_FRICTION_POINTS,
    RESERVE_POLICY_BASELINES,
)
from app.services.agents.source_refs import (
    DRILL_PREP_REFERENCES,
    MARADMIN_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)
from app.services.agents.staff_advisor_agent import _detect_scenario

_COS_REFERENCES = (*DRILL_PREP_REFERENCES, *MARADMIN_REFERENCES)


class ChiefOfStaffAideAgent(Agent):
    metadata = AgentMetadata(
        id="chief-of-staff",
        name="Chief of Staff",
        description=(
            "Senior staff coordinator — battle rhythm, continuity, due-outs, brief posture, turnover, "
            "the standing drill-prep timeline (pre/during/post drill), MARADMIN awareness, calendar/email "
            "triage, and session handoff watch items. Absorbed the former Drill Prep Calendar lane."
        ),
        domain="staff coordination and command-post continuity",
        intended_users=["SMCR officers", "staff officers", "command teams", "company staff", "battalion staff"],
        allowed_sources=[
            "local session handoff",
            "local calendar provider",
            "future user-approved email provider",
            "MARADMIN and MCPEL public sources",
            "public training requirements",
            "local context uploads",
        ],
        disallowed_inputs=[
            "classified information",
            "CUI in unapproved environments",
            "secrets or credentials",
            "calendar tokens",
            "private data not required for task management",
            "sensitive operational plans",
        ],
        system_prompt=(
            "Act as an advisory Chief of Staff/Aide de Camp. Coordinate reminders, ask clarifying questions, "
            "flag PME/FitRep/admin gaps, turn drill dates into practical preparation timelines, and route staff "
            "questions to the right agents. Never provide official guidance.\n\n"
            + RESERVE_ADMIN_SYSTEMS
            + "\n"
            + RESERVE_POLICY_BASELINES
            + "\n"
            + RESERVE_FRICTION_POINTS
            + "\n"
            + NAVY_RESERVE_ADMIN
            + "\n"
            "Reserve continuity friction: 28-day gaps between drills break admin chains; "
            "handoff notes and due-out trackers are the only bridge.\n\n"
            "SCENARIO MODE: If the user provides a specific scenario (country, event type, forces, "
            "timeline, or situation details), produce a prioritized watch list and action items "
            "for the command team — not a drill-prep template."
        ),
    )

    def _is_scenario(self, input_text: str) -> bool:
        return _detect_scenario(input_text)

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        if self._is_scenario(input_text):
            return self._scenario_response(input_text, context)

        handoff = context.extra.get("handoff", {})
        if not isinstance(handoff, dict):
            handoff = {}

        pme_lines = _format_list(handoff, "pme", "No PME watch items supplied.")
        fitrep_lines = _format_list(handoff, "fitreps", "No FitRep watch items supplied.")
        drill_lines = _format_list(handoff, "drill_dates", "No annual drill dates supplied.")
        recurring_lines = _format_list(handoff, "recurring_checks", "No recurring readiness/admin checks supplied.")
        admin_lines = _format_list(handoff, "admin_watch_items", "No admin watch items supplied.")

        answer = (
            "Chief of Staff advisory brief.\n\n"
            "Use this to shape the drill-prep rhythm and the command-post battle rhythm, not as an official "
            "calendar or tasking authority.\n\n"
            "Immediate triage:\n"
            "- Confirm the next drill date and what must be true by first formation.\n"
            "- Review MARADMIN/news tags for Reserve, Officer, PME, Uniform, Training, Admin, Travel, Pay, Fitness, "
            "Awards, Safety, and Doctrine relevance.\n"
            "- Pull suspense items from the calendar and any approved email search results once those "
            "connectors are enabled.\n\n"
            "Standing drill-prep timeline (adjust to the unit SOP):\n"
            "Pre-drill (T-14 to T-1):\n"
            "- Confirm drill date, travel requirements, and must-hit suspense items.\n"
            "- Verify MOL access, LES accuracy, and medical readiness (dental, PHA, IMR).\n"
            "- Check DTS: prior voucher settled? New authorization needed?\n"
            "- Uniform, gear, and required annual training (MarineNet) complete.\n"
            "- MROWS: any ADT/AT orders pending approval? Navy personnel: NROWS submitted (T-60 lead)?\n"
            "During drill:\n"
            "- Drill Manager attendance captured accurately (drives pay).\n"
            "- Capture action items while the right people are present.\n"
            "- FitRep counseling, awards routing, admin corrections — do it now or it waits 28 days.\n"
            "Post-drill (release + 5 days):\n"
            "- DTS voucher completion (most common drop).\n"
            "- Handoff notes updated for continuity between drills.\n"
            "- Unresolved admin items tracked with owners and deadlines.\n\n"
            "Command-and-staff rhythm:\n"
            "- Keep a visible battle rhythm for running estimates, CUBs, CPBs, and commander decision points.\n"
            "- Force assumption, decision, and due-out logs to survive between drills.\n"
            "- Route planning problems toward deliberate MCPP when the staff still lacks shared understanding.\n\n"
            "Continuity and turnover:\n"
            "- Maintain a rolling due-out tracker that survives drill-to-drill gaps.\n"
            "- Brief posture: who needs to know what before the next drill weekend.\n"
            "- Turnover checklist: hot items, open suspenses, commander guidance, pending decisions.\n"
            "- Staff section health: which sections are manned, which are single-threaded.\n\n"
            f"PME watch items:\n{pme_lines}\n\n"
            f"FitRep watch items:\n{fitrep_lines}\n\n"
            f"Stored drill dates:\n{drill_lines}\n\n"
            f"Recurring checks:\n{recurring_lines}\n\n"
            f"Admin watch items:\n{admin_lines}\n\n"
            "Recommended routing:\n"
            "- Drill/admin readiness: Chief of Staff, XO, 1stSgt/SgtMaj, S-1/G-1.\n"
            "- Training or exercise idea: XO, OpsO/S-3/G-3, ORM.\n"
            "- Information environment or public-source question: S-2/G-2 with OSINT source-evaluation support.\n"
            "- Logistics, movement, or LCE support: S-4/G-4.\n"
            "- FitRep or award write-ups: Writing / Briefing Coach (FitRep & awards mode).\n\n"
            "Connectors and bounded capabilities: local session handoff and ICS calendar are live; email and "
            "external calendar connectors are stubs. Travel/GTCC, FitRep, goal, and cadence entries are appended "
            "only when you ask, each with an Undo token; inferred document imports are proposals for review. "
            "No unrestricted filesystem, shell, credential, or silent replace/delete capability exists."
        )

        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(_COS_REFERENCES),
            structured_citations=structured_citations(_COS_REFERENCES),
            source_trust=source_trust_markers(
                _COS_REFERENCES,
                notes_prefix=(
                    "Verify local drill dates, command rhythm, and current travel-admin guidance before execution."
                ),
            ),
            follow_up_questions=_follow_up_questions(handoff),
            confidence=_confidence(handoff),
        )

    def _scenario_response(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        from app.services.agents.staff_advisor_agent import (
            _prior_assessment_context,
            _try_llm_populate,
        )

        prior_context = _prior_assessment_context(context)
        template = (
            "Chief of Staff — SCENARIO ASSESSMENT\n\n"
            "A specific scenario was detected. Use this framework to build the "
            "command team's watch list and action items.\n\n"
            "COMMANDER'S WATCH LIST:\n\n"
            "1. IMMEDIATE ACTIONS (first 24 hours):\n"
            "   - Identify decisions the commander must make immediately\n"
            "   - Determine which staff estimates are needed and from whom\n"
            "   - Identify required higher HQ reporting\n"
            "   - Determine what liaison must be established immediately\n\n"
            "2. STAFF TASKING:\n"
            "   - S-2: Develop intelligence requirements specific to this scenario\n"
            "   - S-3: Develop operations planning requirements\n"
            "   - S-4: Develop logistics assessment requirements\n"
            "   - S-6: Develop communications planning requirements\n"
            "   - G-9/CMO: Develop civil-military coordination requirements\n"
            "   - PAO: Determine public affairs posture for this scenario\n\n"
            "3. DECISION POINTS:\n"
            "   - Identify time-sensitive decisions\n"
            "   - Determine what information the commander needs before each decision\n"
            "   - Recommend the battle rhythm for this scenario\n\n"
            "4. COORDINATION REQUIREMENTS:\n"
            "   - Higher HQ: Identify required reporting and requests\n"
            "   - Adjacent units: Determine who needs to know and what\n"
            "   - Interagency: Assess Embassy/Country Team, DoS/DHR, and NGO coordination needs "
            "(see docs/interagency_reference.md for command relationships and liaison mechanics)\n"
            "   - Coalition/partner nation: Identify required coordination\n\n"
            "5. RISK WATCH:\n"
            "   - Identify the assumption that breaks the plan if wrong\n"
            "   - Assess which staff section is single-threaded or undermanned for this scenario\n"
            "   - Evaluate continuity risk if this extends past the drill weekend\n"
            "   - Determine the commander's decision point for escalation\n\n"
            "6. RECOMMENDED BATTLE RHYTHM:\n"
            "   - Recommend CUB timing and attendees\n"
            "   - Recommend staff sync timing\n"
            "   - Set reporting windows to higher\n"
            "   - Schedule decision briefs\n"
            f"{prior_context}"
        )
        population = _try_llm_populate(
            template,
            input_text,
            self.metadata.system_prompt or "",
            CoSScenarioOutput,
            "cos",
            context,
        )
        return self._response(
            answer=population.answer,
            input_text=input_text,
            citations=citation_titles(_COS_REFERENCES),
            structured_citations=structured_citations(_COS_REFERENCES),
            source_trust=source_trust_markers(_COS_REFERENCES),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What forces are available and what is their current readiness?",
                "What is the commander's initial guidance or intent?",
                "What higher HQ tasking or timeline are we working to?",
                "What interagency or coalition coordination is already in place?",
            ],
            scenario_output=population.scenario_output,
            scenario_output_status=population.status,
            additional_warnings=population.warnings,
            allow_warning_override=population.allow_warning_override,
        )


def _confidence(handoff: dict) -> Confidence:  # type: ignore[type-arg]
    """Confidence scales with how much handoff data is present."""
    if not handoff:
        return Confidence.low
    populated = sum(
        [
            bool(handoff.get("pme")),
            bool(handoff.get("fitreps")),
            bool(handoff.get("drill_dates")),
            bool(handoff.get("admin_watch_items")),
        ]
    )
    if populated >= 3:
        return Confidence.medium
    return Confidence.low


def _follow_up_questions(handoff: dict) -> list[str]:  # type: ignore[type-arg]
    """Generate up to 4 targeted questions: context-specific first, then gap-fill."""
    questions: list[str] = []

    pme = handoff.get("pme") or []
    fitreps = handoff.get("fitreps") or []
    drill_dates = handoff.get("drill_dates") or []
    admin_items = handoff.get("admin_watch_items") or []
    recurring = handoff.get("recurring_checks") or []

    # Context-specific questions when data is present (most actionable)
    if drill_dates:
        next_drill = _first_str(drill_dates, "drill_date")
        questions.append(f"Drill date on record: {next_drill} — should we generate a drill-prep plan?")
    if pme:
        program = _first_str(pme, "program")
        questions.append(f"Is {program!r} on track? Any completion certificates to log?")
    if fitreps:
        occasion = _first_str(fitreps, "occasion")
        due = _first_str(fitreps, "due_date")
        due_text = f", due {due}" if due and due != "None" else ""
        questions.append(f"FitRep for {occasion!r}{due_text} — ready to draft talking points?")
    if admin_items and isinstance(admin_items, list):
        questions.append(f"Most urgent admin item: {admin_items[0]!r} — what's the suspense date?")

    # Gap-filling questions for missing sections
    if not drill_dates:
        questions.append("What is the next drill date and what must be true by first formation?")
    if not pme:
        questions.append("What PME programs are you enrolled in or targeting for promotion?")
    if not fitreps:
        questions.append("When is your next FitRep due, and who is your reporting senior?")
    if not admin_items:
        questions.append("What admin items should be tracked heading into next drill?")
    if not recurring:
        questions.append("Which recurring checks should become standing reminders every drill weekend?")

    return questions[:4]


def _first_str(items: list, key: str) -> str:  # type: ignore[type-arg]
    if not items:
        return "unknown"
    first = items[0]
    if isinstance(first, dict):
        return str(first.get(key, "unknown"))
    return str(first)


def build_chief_of_staff_agent() -> ChiefOfStaffAideAgent:
    return ChiefOfStaffAideAgent()


def _format_list(handoff: object, key: str, empty: str) -> str:
    if not isinstance(handoff, dict):
        return f"- {empty}"
    value = handoff.get(key, [])
    if not isinstance(value, list) or not value:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in value)
