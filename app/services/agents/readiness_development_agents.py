from __future__ import annotations

import re

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.schemas.fitness import FitnessObjective, UnitPtPlan, UnitPtPlanRequest
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    FAMILY_READINESS_REFERENCES,
    FINANCIAL_READINESS_REFERENCES,
    FITNESS_REFERENCES,
    GTCC_REFERENCES,
    WARRIOR_MONK_REFERENCES,
    SourceRef,
    citation_titles,
    source_trust_markers,
    structured_citations,
)
from app.services.fitness.unit_pt_planner import build_unit_pt_plan


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


def build_family_deployment_readiness_agent() -> Agent:
    return ReadinessDevelopmentAgent(
        metadata=AgentMetadata(
            id="family-deployment-readiness-advisor",
            name="Family & Deployment Readiness Advisor",
            description=("Builds household-readiness checklists for extended AT through long overseas absences."),
            domain="family and deployment readiness",
            intended_users=["reserve Marines", "service members", "unit leaders"],
            allowed_sources=[ref.title for ref in FAMILY_READINESS_REFERENCES],
            disallowed_inputs=[
                "SSNs or dependent identity records",
                "medical records or diagnoses",
                "legal-document contents",
                "mission details or precise movement and return details",
                "account credentials or financial account numbers",
            ],
            system_prompt=(
                "Tailor local checklists using duration and broad household needs. Track actions, not sensitive "
                "contents. Route legal, medical, financial, and command determinations to qualified support."
            ),
        ),
        references=FAMILY_READINESS_REFERENCES,
        answer=(
            "Family and deployment readiness advisory draft.\n\n"
            "Use the Bench+Files readiness checklist to track unit coordination, legal-assistance review, "
            "power of attorney questions for qualified counsel, DEERS and ID-card checks, public or "
            "user-approved contacts, household continuity, communication, OPSEC, and reintegration. "
            "The checklist can scale from extended AT to approximately a year away.\n\n"
            "Do not enter mission, movement, SSN, medical, account, or legal-document details.\n\n"
            "DRAFT — Verify all references against current official sources before acting."
        ),
        questions=[
            "What is the approximate duration or absence window?",
            "Which broad household responsibilities require continuity?",
            "Which checklist areas are already complete?",
        ],
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


class FitnessPlanningAgent(Agent):
    """Builds a scaled unit-PT draft in chat from a plain-language request.

    Parses the participant count, objective, and duration out of the request
    (defaulting the rest and stating every assumption), runs the deterministic
    unit-PT engine, and renders the scaled organization, blocks, staff reviews,
    and ORM matrix inline. No official-event or medical authority is claimed.
    """

    def __init__(self, *, metadata: AgentMetadata, references: tuple[SourceRef, ...], questions: list[str]) -> None:
        self.metadata = metadata
        self.references = references
        self.questions = questions

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        request, assumptions = _parse_unit_pt_request(input_text)
        plan = build_unit_pt_plan(request)
        return self._response(
            answer=_render_unit_pt_plan(plan, assumptions),
            input_text=input_text,
            citations=citation_titles(self.references),
            structured_citations=structured_citations(self.references),
            source_trust=source_trust_markers(self.references),
            confidence=Confidence.medium,
            follow_up_questions=self.questions,
        )


def build_fitness_planning_agent() -> Agent:
    return FitnessPlanningAgent(
        metadata=AgentMetadata(
            id="fitness-planning-advisor",
            name="Fitness Planning Advisor",
            description="Designs scalable PFT/CFT and unit-PT drafts for 5–50 Marines with staff and ORM review.",
            domain="unit fitness planning",
            intended_users=["unit leaders", "S-3", "S-4", "SgtMaj/SEL", "FFI/CPTR coordinators"],
            allowed_sources=[ref.title for ref in FITNESS_REFERENCES],
            disallowed_inputs=["medical diagnoses", "rehabilitation prescriptions", "official risk acceptance"],
            system_prompt=(
                "Build a scaled unit-PT draft from the request. Read participant count (5–50), objective, and time; "
                "default location, equipment, ability, and conditions when unstated and name every assumption. Return "
                "scaled organization, blocks, S-3/S-4/SEL/ORM reviews, and an editable ORM matrix without claiming "
                "official-event, medical, or risk-acceptance authority."
            ),
        ),
        references=FITNESS_REFERENCES,
        questions=[
            "How many Marines (5–50), what objective (PFT/CFT/general/strength/endurance/mobility), and how much time?",
            "What location, equipment, ability limitations, and current weather/site constraints apply?",
            "Should the plan use a clean or user-approved adult cadence from the local library?",
        ],
    )


def _parse_unit_pt_request(input_text: str) -> tuple[UnitPtPlanRequest, list[str]]:
    lower = input_text.lower()
    assumptions: list[str] = []

    count = _extract_count(input_text, lower)
    if count is None:
        count = 20
        assumptions.append("Participant count not stated — assumed 20 Marines (say e.g. '30 Marines').")

    objective = _extract_objective(lower)
    if objective is None:
        objective = FitnessObjective.general
        assumptions.append(
            "Objective not stated — assumed general fitness (PFT/CFT/strength/endurance/mobility also supported)."
        )

    duration = _extract_duration(lower)
    if duration is None:
        duration = 60
        assumptions.append("Duration not stated — assumed 60 minutes (20–120 supported).")

    assumptions.append(
        "Location, equipment, ability notes, and conditions used safe defaults — tell me the real ones to refine."
    )
    return (
        UnitPtPlanRequest(participant_count=count, objective=objective, duration_minutes=duration),
        assumptions,
    )


def _extract_count(input_text: str, lower: str) -> int | None:
    tied = re.search(r"(\d{1,3})\s*(?:marines|participants|personnel|troops|pax|people|pers)\b", lower)
    if tied and 5 <= int(tied.group(1)) <= 50:
        return int(tied.group(1))
    for match in re.finditer(r"\b(\d{1,3})\b", input_text):
        value = int(match.group(1))
        trailing = lower[match.end() : match.end() + 12].lstrip()
        if 5 <= value <= 50 and not trailing.startswith(("min", "hour", "hr")):
            return value
    return None


def _extract_objective(lower: str) -> FitnessObjective | None:
    if "cft" in lower:
        return FitnessObjective.cft
    if "pft" in lower:
        return FitnessObjective.pft
    if "strength" in lower:
        return FitnessObjective.strength
    if "endurance" in lower or "conditioning" in lower:
        return FitnessObjective.endurance
    if "mobility" in lower or "recovery" in lower or "stretch" in lower:
        return FitnessObjective.mobility
    if "general" in lower:
        return FitnessObjective.general
    return None


def _extract_duration(lower: str) -> int | None:
    minutes = re.search(r"(\d{2,3})\s*(?:mins|min|minutes|minute)\b", lower)
    if minutes:
        return max(20, min(120, int(minutes.group(1))))
    hours = re.search(r"(\d(?:\.\d)?)\s*(?:hours|hour|hrs|hr)\b", lower)
    if hours:
        return max(20, min(120, round(float(hours.group(1)) * 60)))
    return None


def _render_unit_pt_plan(plan: UnitPtPlan, assumptions: list[str]) -> str:
    lines = ["Fitness-planning advisory — unit PT plan draft", ""]
    if assumptions:
        lines.append("Assumptions I made (give me the real values and I'll rebuild):")
        lines.extend(f"- {item}" for item in assumptions)
        lines.append("")
    lines.append(
        f"Snapshot: {plan.participant_count} Marines · {plan.objective.value} · "
        f"{plan.duration_minutes} min · {plan.scaling_band}"
    )
    lines.append("")
    lines.append("Organization:")
    lines.extend(f"- {item}" for item in plan.organization)
    lines.append("")
    lines.append("Session blocks:")
    for block in plan.blocks:
        lines.append(f"- {block.name} ({block.minutes} min): {' '.join(block.instructions)}")
        if block.scaling:
            lines.append(f"  Scaling: {'; '.join(block.scaling)}")
    if plan.cadence:
        lines.extend(["", f"Cadence: {plan.cadence}"])
    lines.extend(["", "Staff reviews:"])
    for review in plan.staff_reviews:
        lines.append(f"- {review.role}: {' '.join([*review.findings, *review.actions])}")
    lines.extend(["", "ORM matrix:"])
    for hazard in plan.orm.hazards:
        lines.append(
            f"- {hazard.hazard} (initial {hazard.initial_risk} → residual {hazard.residual_risk}) · owner {hazard.owner}"
        )
        lines.append(f"  Controls: {'; '.join(hazard.controls)}. Stop-work: {hazard.stop_trigger}")
    lines.append(f"({plan.orm.acceptance_note})")
    lines.extend(["", "Warnings:"])
    lines.extend(f"- {item}" for item in plan.warnings)
    lines.extend(
        [
            "",
            "This advisor is not an FFI, CPTR, medical provider, or official PFT/CFT monitor. Qualified personnel "
            "and the chain of command must validate official events, restrictions, and residual-risk acceptance.",
            "",
            plan.footer,
        ]
    )
    return "\n".join(lines)


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
