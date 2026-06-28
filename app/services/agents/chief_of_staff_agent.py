from __future__ import annotations

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext

_COS_SCENARIO_SIGNALS = (
    "earthquake", "hurricane", "typhoon", "tsunami", "flood", "wildfire",
    "fhadr", "ha/dr", "disaster", "humanitarian",
    "exercise", "scenario", "vignette", "situation",
    "invasion", "insurgency", "conflict", "crisis", "coup",
    "partner nation", "host nation", "embassy", "country team",
    "meu", "jt", "jtf", "joint task force", "coalition",
    "noncombatant evacuation", "neo",
    "casualties", "displaced", "refugees",
)


class ChiefOfStaffAideAgent(Agent):
    metadata = AgentMetadata(
        id="chief-of-staff",
        name="Chief of Staff",
        description=(
            "Senior staff coordinator — battle rhythm, continuity, due-outs, brief posture, turnover, "
            "drill weekend prep, MARADMIN awareness, calendar/email triage, and session handoff watch items."
        ),
        domain="staff coordination and command-post continuity",
        intended_users=["SMCR officers", "staff officers", "command teams"],
        allowed_sources=[
            "local session handoff",
            "local calendar provider",
            "future user-approved email provider",
            "MARADMIN and MCPEL public sources",
            "local context uploads",
        ],
        disallowed_inputs=[
            "classified information",
            "CUI in unapproved environments",
            "secrets or credentials",
            "private data not required for task management",
            "sensitive operational plans",
        ],
        system_prompt=(
            "Act as an advisory Chief of Staff/Aide de Camp. Coordinate reminders, ask clarifying questions, "
            "flag PME/FitRep/admin gaps, and route staff questions to the right agents. "
            "Never provide official guidance.\n\n"
            "Admin system chain awareness:\n"
            "- Drill Manager → IDT pay (attendance errors delay entire cycle).\n"
            "- MROWS → ADT/AT orders (needs lead time for approval chain).\n"
            "- DTS → travel vouchers (most common post-drill drop).\n"
            "- MOL → self-service (LES, OMPF, training records).\n"
            "- MCTFS/Unit Diary → authoritative status changes.\n"
            "- MRRS/RHRP/PHA → medical readiness tracking.\n\n"
            "AT planning triggers: T-45 (MROWS submission), T-30 (DTS authorization), "
            "T-15 (final coordination, billeting, ranges).\n\n"
            "Reserve continuity friction: 28-day gaps between drills break admin chains; "
            "handoff notes and due-out trackers are the only bridge.\n\n"
            "SCENARIO MODE: If the user provides a specific scenario (country, event type, forces, "
            "timeline, or situation details), produce a prioritized watch list and action items "
            "for the command team — not a drill-prep template."
        ),
    )

    def _is_scenario(self, input_text: str) -> bool:
        lowered = input_text.lower()
        return any(s in lowered for s in _COS_SCENARIO_SIGNALS)

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
            "Immediate triage:\n"
            "- Check next drill date and generate/update drill-prep plan.\n"
            "- Review MARADMIN/news tags for Reserve, Officer, PME, Uniform, Training, Admin, Travel, Pay, Fitness, "
            "Awards, Safety, and Doctrine relevance.\n"
            "- Review user-approved calendar events for suspense items once calendar access is connected.\n"
            "- Review user-approved email search results for action items once email access is connected.\n\n"
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
            "- Drill/admin readiness: Chief of Staff/Aide, XO, 1stSgt/SgtMaj, S-1/G-1.\n"
            "- Training or exercise idea: XO, OpsO/S-3/G-3, Training Planner, ORM.\n"
            "- Information environment or public-source question: S-2/G-2 with OSINT source-evaluation support.\n"
            "- Logistics or movement support: S-4/G-4 and logistics sources.\n\n"
            "Connector status:\n"
            "- Email: provider interface exists; live access is not enabled.\n"
            "- Calendar: local ICS exists; Microsoft Graph and Google Calendar remain stubs.\n"
            "- Session handoff: local JSON persistence exists for minimum necessary user context."
        )

        return self._response(
            answer=answer,
            input_text=input_text,
            follow_up_questions=_follow_up_questions(handoff),
            confidence=_confidence(handoff),
        )


    def _scenario_response(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Chief of Staff — SCENARIO ASSESSMENT\n\n"
            "A specific scenario was provided. Producing a command-team watch list "
            "and action items rather than a drill-prep template.\n\n"
            "COMMANDER'S WATCH LIST:\n\n"
            "1. IMMEDIATE ACTIONS (first 24 hours):\n"
            "   - What decisions does the commander need to make NOW?\n"
            "   - What staff estimates are needed and from whom?\n"
            "   - What higher HQ reporting is required?\n"
            "   - What liaison must be established immediately?\n\n"
            "2. STAFF TASKING:\n"
            "   - S-2: [intelligence requirements for this scenario]\n"
            "   - S-3: [operations planning requirements]\n"
            "   - S-4: [logistics assessment requirements]\n"
            "   - S-6: [communications planning requirements]\n"
            "   - G-9/CMO: [civil-military coordination requirements]\n"
            "   - PAO: [public affairs posture for this scenario]\n\n"
            "3. DECISION POINTS:\n"
            "   - What decisions are time-sensitive?\n"
            "   - What information does the commander need before each decision?\n"
            "   - What is the recommended battle rhythm for this scenario?\n\n"
            "4. COORDINATION REQUIREMENTS:\n"
            "   - Higher HQ: what reporting and requests are needed?\n"
            "   - Adjacent units: who needs to know and what?\n"
            "   - Interagency: Embassy/Country Team, DoS/DHR, NGOs?\n"
            "   - Coalition/partner nation: what coordination is required?\n\n"
            "5. RISK WATCH:\n"
            "   - What assumption breaks the plan if wrong?\n"
            "   - What staff section is single-threaded or undermanned for this?\n"
            "   - What continuity risk exists if this extends past the drill weekend?\n"
            "   - What is the commander's decision point for escalation?\n\n"
            "6. RECOMMENDED BATTLE RHYTHM:\n"
            "   - CUB timing and attendees\n"
            "   - Staff sync timing\n"
            "   - Reporting windows to higher\n"
            "   - Decision brief schedule\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            confidence=Confidence.medium,
            follow_up_questions=[
                "What forces are available and what is their current readiness?",
                "What is the commander's initial guidance or intent?",
                "What higher HQ tasking or timeline are we working to?",
                "What interagency or coalition coordination is already in place?",
            ],
        )


def _confidence(handoff: dict) -> Confidence:  # type: ignore[type-arg]
    """Confidence scales with how much handoff data is present."""
    if not handoff:
        return Confidence.low
    populated = sum([
        bool(handoff.get("pme")),
        bool(handoff.get("fitreps")),
        bool(handoff.get("drill_dates")),
        bool(handoff.get("admin_watch_items")),
    ])
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
        questions.append("What are your upcoming drill weekend dates?")
    if not pme:
        questions.append("What PME programs are you enrolled in or targeting for promotion?")
    if not fitreps:
        questions.append("When is your next FitRep due, and who is your reporting senior?")
    if not admin_items:
        questions.append("What admin items should be tracked heading into next drill?")
    if not recurring:
        questions.append("What checks should repeat every drill weekend (ammo account, training schedule, claims)?")

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
