from __future__ import annotations

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    FINANCIAL_READINESS_REFERENCES,
    FITNESS_REFERENCES,
    GTCC_REFERENCES,
    WARRIOR_MONK_REFERENCES,
    SourceRef,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class ReadinessDevelopmentAgent(Agent):
    def __init__(
        self,
        *,
        metadata: AgentMetadata,
        references: tuple[SourceRef, ...],
        answer: str,
        questions: list[str],
    ) -> None:
        self.metadata = metadata
        self.references = references
        self.answer = answer
        self.questions = questions

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        context_lines = self._active_context_lines(context)
        context_note = "\n\n" + "\n".join(context_lines) if context_lines else ""
        return self._response(
            answer=self.answer + context_note,
            input_text=input_text,
            citations=citation_titles(self.references),
            structured_citations=structured_citations(self.references),
            source_trust=source_trust_markers(self.references),
            confidence=Confidence.medium,
            follow_up_questions=self.questions,
        )


def build_gtcc_advisor_agent() -> Agent:
    return ReadinessDevelopmentAgent(
        metadata=AgentMetadata(
            id="gtcc-advisor",
            name="GTCC Advisor",
            description="Helps users track cardholder actions and troubleshoot GTCC program friction.",
            domain="government travel charge card",
            intended_users=["GTCC cardholders", "reserve Marines", "travel administrators"],
            allowed_sources=[ref.title for ref in GTCC_REFERENCES],
            disallowed_inputs=["full card numbers", "CVV", "passwords", "bank credentials", "CUI or PII"],
            system_prompt=(
                "Keep GTCC help separate from personal financial advice. Reduce friction with direct official links, "
                "clear next actions, and reminders that user-entered balances may be stale. Never request credentials."
            ),
        ),
        references=GTCC_REFERENCES,
        answer=(
            "GTCC advisory draft.\n\n"
            "Use the Travel & GTCC workspace to log charges, receipts, notes, payments, and the date you last checked "
            "the account. That tracker is user-entered and is not a live bank balance.\n\n"
            "Fast path:\n"
            "- Open CitiManager: https://home.cards.citidirect.com/CommercialCard/login\n"
            "- Compare the displayed balance and transactions with the trip ledger.\n"
            "- Record the check date, balance, and payment status in the trip folder.\n"
            "- For declined cards, split disbursement, delinquency, or mission-critical status, use the current DoD "
            "GTCC guidance and contact the unit APC/card issuer through official channels.\n"
            "- Never paste a card number, CVV, password, or authentication code into this application."
        ),
        questions=[
            "Is this an account-access, declined-card, voucher/payment, or reconciliation problem?",
            "When did you last verify the balance directly in CitiManager?",
        ],
    )


def build_financial_readiness_agent() -> Agent:
    return ReadinessDevelopmentAgent(
        metadata=AgentMetadata(
            id="financial-readiness-advisor",
            name="Financial Readiness Advisor",
            description="Builds practical personal-finance checklists using official military resources.",
            domain="personal financial readiness",
            intended_users=["service members", "reserve Marines", "families"],
            allowed_sources=[ref.title for ref in FINANCIAL_READINESS_REFERENCES],
            disallowed_inputs=["account credentials", "full account numbers", "tax IDs", "regulated investment orders"],
            system_prompt=(
                "Keep personal financial readiness separate from GTCC administration. Explain LES, myPay, budget, "
                "debt, emergency savings, and TSP resources without acting as a fiduciary, tax professional, or lender."
            ),
        ),
        references=FINANCIAL_READINESS_REFERENCES,
        answer=(
            "Financial-readiness advisory draft.\n\n"
            "Start with the decision, not a product pitch:\n"
            "- Pay accuracy: compare the current LES with orders, drills, allowances, deductions, and leave; route "
            "discrepancies through the servicing admin/finance office.\n"
            "- Cash flow: list essential monthly obligations, irregular reserve income, and the next 30 days of due dates.\n"
            "- Resilience: identify a realistic emergency-fund step and a debt-payment priority you can sustain.\n"
            "- Future: use official TSP and FINRED material before changing contribution or investment choices.\n"
            "- Expert help: Military OneSource offers financial counseling; use a qualified tax, legal, or financial "
            "professional for individualized advice.\n\n"
            "This lane does not administer or reconcile GTCC accounts; use the GTCC Advisor for that."
        ),
        questions=[
            "Is the immediate issue LES/pay accuracy, monthly cash flow, debt, emergency savings, or TSP planning?",
            "What decision must be made, and by when?",
        ],
    )


def build_fitness_planning_agent() -> Agent:
    return ReadinessDevelopmentAgent(
        metadata=AgentMetadata(
            id="fitness-planning-advisor",
            name="Fitness Planning Advisor",
            description="Designs scalable PFT/CFT and unit-PT drafts for 5–50 Marines with staff and ORM review.",
            domain="unit fitness planning",
            intended_users=["unit leaders", "S-3", "S-4", "SgtMaj/SEL", "FFI/CPTR coordinators"],
            allowed_sources=[ref.title for ref in FITNESS_REFERENCES],
            disallowed_inputs=["medical diagnoses", "rehabilitation prescriptions", "official risk acceptance"],
            system_prompt=(
                "Use the typed unit-PT planner for structured plans. Ask participant count, objective, time, location, "
                "equipment, ability/limitations, conditions, and cadence preference. Coordinate S-3, S-4, SEL, and ORM."
            ),
        ),
        references=FITNESS_REFERENCES,
        answer=(
            "Fitness-planning advisory draft.\n\n"
            "For a unit plan, open Unit PT Planner and provide: 5–50 participants, PFT/CFT/general objective, available "
            "time and site, equipment, mixed-ability or medical limitations, current conditions, and whether you want "
            "a cadence from the local library. The planner returns scaled lanes/stations, S-3/S-4/SgtMaj reviews, and "
            "an editable ORM matrix.\n\n"
            "This advisor is not an FFI, CPTR, medical provider, or official PFT/CFT monitor. Qualified personnel and "
            "the chain of command must validate official events, restrictions, and residual-risk acceptance."
        ),
        questions=[
            "How many Marines (5–50), what objective, and how much time?",
            "What location, equipment, ability limitations, and current weather/site constraints apply?",
            "Should the plan use a clean or user-approved adult cadence from the local library?",
        ],
    )


def build_warrior_monk_agent() -> Agent:
    return ReadinessDevelopmentAgent(
        metadata=AgentMetadata(
            id="warrior-monk",
            name="Warrior-Monk",
            description="A philosophical reflection partner grounded in MCDP 1, Leading Marines, and MCU resources.",
            domain="professional reflection and moral purpose",
            intended_users=["Marines", "leaders", "PME facilitators"],
            allowed_sources=[ref.title for ref in WARRIOR_MONK_REFERENCES],
            disallowed_inputs=[
                "clinical counseling",
                "religious direction",
                "legal findings",
                "disciplinary decisions",
            ],
            system_prompt=(
                "Be austere, candid, historically literate, and humane: Marcus Aurelius meets General Mattis in tone, "
                "without impersonating either or inventing quotes. Focus on moral purpose, disciplined reflection, and action."
            ),
        ),
        references=WARRIOR_MONK_REFERENCES,
        answer=(
            "Warrior-Monk reflection draft.\n\n"
            "Strip the problem to what you control, what duty requires, and what fear or vanity is trying to disguise. "
            "MCDP 1 treats uncertainty, friction, and human will as permanent features—not excuses. Leading Marines asks "
            "for moral character expressed through conduct.\n\n"
            "Reflection drill:\n"
            "- Name the hard fact without drama.\n"
            "- Separate obligation from appetite and reputation.\n"
            "- Identify the Marine or institution that bears the cost of delay.\n"
            "- Choose the smallest honorable action that changes reality today.\n"
            "- Set a time to examine the result without self-deception.\n\n"
            "For command programs, counseling mechanics, family support, or the full six MLD areas, hand this to the "
            "Leadership Advisor. This lane is reflection, not therapy, chaplaincy, legal advice, or command authority."
        ),
        questions=[
            "What fact are you reluctant to state plainly?",
            "Which duty is actually yours, and what is outside your control?",
            "What concrete action would make this reflection useful by tomorrow?",
        ],
    )
