from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext


class ChiefOfStaffAideAgent(Agent):
    metadata = AgentMetadata(
        id="chief-of-staff-aide",
        name="Chief of Staff / Aide de Camp",
        description=(
            "Coordinates drill weekend prep, general news, MARADMIN awareness, calendar/email task triage, "
            "and user session handoff watch items."
        ),
        domain="staff coordination",
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
            "Never provide official guidance."
        ),
    )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        handoff = context.extra.get("handoff", {})
        pme_lines = _format_list(handoff, "pme", "No PME watch items supplied.")
        fitrep_lines = _format_list(handoff, "fitreps", "No FitRep watch items supplied.")
        drill_lines = _format_list(handoff, "drill_dates", "No annual drill dates supplied.")
        recurring_lines = _format_list(handoff, "recurring_checks", "No recurring readiness/admin checks supplied.")
        admin_lines = _format_list(handoff, "admin_watch_items", "No admin watch items supplied.")

        answer = (
            "Chief of Staff / Aide de Camp advisory brief.\n\n"
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
            follow_up_questions=[
                "What is the next drill date?",
                "Which mailbox/calendar provider should be connected first?",
                "What PME, FitRep, or admin suspense should be added to the handoff?",
                "Which staff echelon should vet this idea: company, battalion, or division/group?",
            ],
            confidence=Confidence.low,
        )


def build_chief_of_staff_agent() -> ChiefOfStaffAideAgent:
    return ChiefOfStaffAideAgent()


def _format_list(handoff: object, key: str, empty: str) -> str:
    if not isinstance(handoff, dict):
        return f"- {empty}"
    value = handoff.get(key, [])
    if not isinstance(value, list) or not value:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in value)
