"""Consolidated staff advisor agents with echelon modifier.

Instead of 55 separate StaffRoleDefinition rows (one per role per echelon),
this module defines ~15 StaffRoleArchetype rows.  Each archetype represents a
staff *function* (XO, OpsO, S-4, Safety …).  Echelon is a runtime parameter
pulled from AgentContext or the user's profile — the archetype's ``run()``
adapts scope language, product names, and terminology accordingly.

The echelon modifier lives in ``ECHELON_CONTEXT`` and ``_echelon_adapt()``.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.schemas.staff import MagtfLens, StaffEchelon, StaffRoleMetadata
from app.services.agents.base import Agent, AgentContext
from app.services.agents.osint_agent import build_osint_agent
from app.services.agents.source_refs import (
    FORCE_PROTECTION_REFERENCES,
    G8_REFERENCES,
    G9_REFERENCES,
    IG_REFERENCES,
    LEADERSHIP_REFERENCES,
    LEGAL_REFERENCES,
    MEDICAL_REFERENCES,
    MOS_0102_REFERENCES,
    MOS_0202_REFERENCES,
    MOS_0402_REFERENCES,
    MOS_0430_REFERENCES,
    MOS_0511_REFERENCES,
    MOS_3002_REFERENCES,
    MOS_4402_REFERENCES,
    PAO_REFERENCES,
    S1_REFERENCES,
    S2_REFERENCES,
    S3_REFERENCES,
    S4_REFERENCES,
    S6_REFERENCES,
    SEL_REFERENCES,
    STAFF_PROCESS_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    SourceRef,
    citation_titles,
    source_trust_markers,
    structured_citations,
)

# ---------------------------------------------------------------------------
# Echelon modifier
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EchelonContext:
    """Terminology and scope modifiers for a given echelon."""
    label: str
    maturity: str
    staff_prefix: str          # "S-" or "G-" for numbered staff
    scope_adjective: str       # e.g. "company-level", "division-level"


ECHELON_CONTEXT: dict[StaffEchelon, EchelonContext] = {
    StaffEchelon.company: EchelonContext(
        label="company",
        maturity="tactical/company",
        staff_prefix="",
        scope_adjective="company-level",
    ),
    StaffEchelon.battalion: EchelonContext(
        label="battalion",
        maturity="battalion staff",
        staff_prefix="S-",
        scope_adjective="battalion-level",
    ),
    StaffEchelon.regiment_meu_wing: EchelonContext(
        label="regiment/MEU/wing",
        maturity="regiment/MEU/wing staff",
        staff_prefix="S-",
        scope_adjective="regiment/MEU/wing-level",
    ),
    StaffEchelon.division_group: EchelonContext(
        label="division/group",
        maturity="division/group staff",
        staff_prefix="G-",
        scope_adjective="division/group-level",
    ),
}

DEFAULT_ECHELON = StaffEchelon.battalion


def _resolve_echelon(context: AgentContext) -> StaffEchelon:
    """Pull echelon from context, falling back to battalion."""
    raw = context.extra.get("echelon")
    if isinstance(raw, StaffEchelon):
        return raw
    if isinstance(raw, str):
        try:
            return StaffEchelon(raw)
        except ValueError:
            pass
    return DEFAULT_ECHELON


# ---------------------------------------------------------------------------
# Role archetypes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StaffRoleArchetype:
    role: str
    title: str
    scope: str
    focus: tuple[str, ...]
    magtf_lenses: tuple[MagtfLens, ...] = (MagtfLens.ce_c2,)
    products: tuple[str, ...] = ()
    osint_enabled: bool = False
    mos_depth: str = ""  # extra MOS-specific content merged from former MOS agents
    references_extra: tuple[SourceRef, ...] = ()  # MOS-specific refs to add


ROLE_ARCHETYPES: tuple[StaffRoleArchetype, ...] = (
    # --- Primary staff ---
    StaffRoleArchetype(
        role="xo",
        title="XO / Executive Officer",
        scope="Staff synchronization, decision support, and commander readiness",
        focus=("feasibility", "staff integration", "risk", "decision points", "task ownership"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("XO sync matrix", "decision support matrix", "due-out tracker"),
    ),
    # chief: merged into standalone chief-of-staff agent
    StaffRoleArchetype(
        role="battle_captain",
        title="Battle Captain / Watch Officer",
        scope="Watchfloor control, command-post picture, and escalation discipline",
        focus=("watchstanding", "status picture", "escalation"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("decision support matrix", "battle captain watchboard", "command update brief"),
    ),
    StaffRoleArchetype(
        role="opso",
        title="OpsO / S-3 / G-3",
        scope="Operations and training planning",
        focus=("scheme", "training value", "staff products", "mission analysis", "timeline"),
        magtf_lenses=(MagtfLens.ce_c2, MagtfLens.gce),
        products=("training plan", "event synchronization matrix", "commander decision brief"),
        mos_depth=(
            "0511 MAGTF Planner depth:\n"
            "- Whether the planning process is actually disciplined enough to trust.\n"
            "- Whether assumptions, tasks, and required section inputs are being captured cleanly.\n"
            "- Whether the OPT is producing decisions or just busy slides.\n"
            "- Whether the plan can survive a handoff between drills without rebuilding from zero."
        ),
        references_extra=MOS_0511_REFERENCES,
    ),
    StaffRoleArchetype(
        role="s1",
        title="S-1 / G-1 / Administration",
        scope="Administration, manpower, and personnel readiness",
        focus=("rosters", "orders", "FitReps", "awards", "accountability", "correspondence"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "admin estimate", "admin task tracker", "routing matrix",
            "pre-drill admin readiness check",
        ),
        mos_depth=(
            "0102 Adjutant depth:\n"
            "- Whether adjutant systems are actually under control instead of just claimed on a tracker.\n"
            "- Whether files, directives, awards, and accountability can survive a gap between drills.\n"
            "- Whether correspondence and staffing actions are being routed cleanly enough to brief the XO.\n"
            "- Whether the unit can answer simple admin questions without a scavenger hunt."
        ),
        references_extra=MOS_0102_REFERENCES,
    ),
    StaffRoleArchetype(
        role="s2",
        title="S-2 / G-2 / Intelligence",
        scope="Intelligence, public-source context, and estimate support",
        focus=("assumptions", "information gaps", "source confidence", "PIR framing"),
        osint_enabled=True,
        mos_depth=(
            "0202 Intelligence Officer depth:\n"
            "- A harder read on whether the intelligence question is tied to a real command decision.\n"
            "- Whether collection, analysis, and briefing effort are being wasted on trivia.\n"
            "- Whether assumptions, gaps, and confidence are visible enough for the XO and commander.\n"
            "- Whether continuity notes will let the next drill pick the estimate back up fast."
        ),
        references_extra=MOS_0202_REFERENCES,
    ),
    StaffRoleArchetype(
        role="s4",
        title="S-4 / G-4 / Logistics",
        scope="Logistics, sustainment, supply accountability, and movement support",
        focus=("transportation", "supply", "maintenance", "supportability", "lead times"),
        magtf_lenses=(MagtfLens.ce_c2, MagtfLens.lce),
        products=(
            "logistics estimate", "support request matrix", "recovery timeline",
        ),
        mos_depth=(
            "0402 Logistics Officer depth:\n"
            "- A harder read on lead times, support priorities, and sustainment assumptions.\n"
            "- The difference between a support request and a supportable plan.\n"
            "0430 Mobility Officer depth:\n"
            "- Whether the force list, lift assumptions, and movement documentation match reality.\n"
            "- Whether embarkation tasks are resourced early enough instead of becoming a last-week panic.\n"
            "3002 Supply Officer depth:\n"
            "- A harder read on supply records, inventory readiness, and command-accountability risk.\n"
            "- Whether the support plan depends on gear that is on paper but not truly serviceable."
        ),
        references_extra=(*MOS_0402_REFERENCES, *MOS_0430_REFERENCES, *MOS_3002_REFERENCES),
    ),
    StaffRoleArchetype(
        role="s6",
        title="S-6 / G-6 / Communications",
        scope="Communications, C2 support, and information management",
        focus=("C2", "PACE", "permissions", "operator readiness"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("PACE plan", "comm plan outline", "radio guard chart"),
        mos_depth=(
            "0602 Communications Officer depth:\n"
            "- Whether the PACE plan is tied to actual reports, users, and decision points.\n"
            "- Whether operators, accounts, equipment, and permissions are ready before drill starts.\n"
            "- Whether rehearsals prove the reporting rhythm instead of only checking gear status.\n"
            "- Whether the plan can survive tired users, missing permissions, or a compressed timeline."
        ),
        references_extra=S6_REFERENCES,
    ),
    StaffRoleArchetype(
        role="sel",
        title="SgtMaj / 1stSgt / Senior Enlisted Leader",
        scope="Standards, accountability, welfare, and discipline",
        focus=("standards", "welfare", "discipline", "accountability", "ceremony"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("troop-flow checklist", "formation/transition matrix", "leader touchpoint plan"),
    ),
    StaffRoleArchetype(
        role="surgeon",
        title="Surgeon / Medical / Doc",
        scope="Medical support, TCCC awareness, casualty planning, and evacuation",
        focus=("casualty response", "CASEVAC", "medical risk", "TCCC"),
        magtf_lenses=(MagtfLens.gce, MagtfLens.lce),
        products=(
            "medical estimate", "CASEVAC / MEDEVAC check",
            "casualty collection logic", "coordination trigger list",
        ),
    ),
    StaffRoleArchetype(
        role="sja",
        title="SJA / Legal",
        scope="Legal issue-spotting, ROE/RUF guardrails, investigations, and command legal routing",
        focus=("legal review", "ROE/RUF", "investigation boundaries", "issue spotting"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("Legal issue-spotter", "ROE/RUF guardrails", "legal review trigger list"),
        mos_depth=(
            "4402 Judge Advocate depth:\n"
            "- Whether the matter is military justice, admin law, legal assistance, ethics, claims, or another lane.\n"
            "- What facts are missing before a lawyer can responsibly advise.\n"
            "- What command action should pause until the SJA or responsible counsel reviews it.\n"
            "- How to preserve clean routing, privilege awareness, and continuity between drills."
        ),
        references_extra=MOS_4402_REFERENCES,
    ),
    StaffRoleArchetype(
        role="pao",
        title="PAO / COMMSTRAT / Information",
        scope="Public affairs, media posture, release authority, OPSEC coordination, and info effects",
        focus=("public posture", "release authority", "OPSEC coordination", "narrative coherence"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "Public affairs plan", "release approval matrix",
            "response-to-query lines", "themes and messages",
        ),
    ),
    # safety: merged into standalone orm-risk-management agent
    StaffRoleArchetype(
        role="chaplain",
        title="Chaplain / Religious Support",
        scope="Religious support, morale, ethical climate, and confidential support boundaries",
        focus=("religious support", "morale", "confidentiality boundaries"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("Religious support plan", "morale and welfare estimate", "confidentiality boundary note"),
    ),
    StaffRoleArchetype(
        role="provost",
        title="Provost Marshal / Security",
        scope="Force protection, access control, traffic control, and security planning",
        focus=("force protection", "access control", "security coordination"),
        magtf_lenses=(MagtfLens.ce_c2, MagtfLens.lce),
        products=("Security annex", "access-control plan", "traffic and parking control plan", "visitor control checklist"),
    ),
    StaffRoleArchetype(
        role="ig",
        title="Inspector General",
        scope="Inspection readiness, inquiry boundaries, impartiality, and readiness trends",
        focus=("inspection readiness", "inquiry boundaries", "impartiality"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("IG inspection touchpoints", "inquiry boundary note", "readiness trend memo"),
    ),
    # aviation: moved to standalone ace agent
    # lce: moved to standalone lce agent
    StaffRoleArchetype(
        role="g8",
        title="G-8 / Resources",
        scope="Resources, fiscal constraints, prioritization, and funding-risk tradeoffs",
        focus=("resources", "prioritization", "funding risk"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("resource estimate", "funding risk note", "priority tradeoff brief", "resourcing decision point"),
    ),
    StaffRoleArchetype(
        role="g9",
        title="G-9 / Civil-Military",
        scope="Civil-military integration, community context, partner coordination, and civil affairs",
        focus=("civil impact", "external coordination", "continuity", "civil reconnaissance"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=("civil situation frame", "partner coordination plan", "continuity note"),
    ),
)


# ---------------------------------------------------------------------------
# Staff advisor agent
# ---------------------------------------------------------------------------

class StaffAdvisorAgent(Agent):
    def __init__(self, archetype: StaffRoleArchetype) -> None:
        self.archetype = archetype
        self.metadata = AgentMetadata(
            id=f"staff-{archetype.role}",
            name=archetype.title,
            description=f"Advisory {archetype.title} perspective for vetting staff ideas. Adapts to any echelon.",
            domain="staff council",
            intended_users=["SMCR officers", "staff officers", "command teams"],
            allowed_sources=[
                "local context",
                "public doctrine manifests",
                "session handoff",
                "OSINT source items when S-2/G-2",
            ],
            disallowed_inputs=[
                "classified information",
                "CUI",
                "sensitive operational details",
                "private personal data",
            ],
            system_prompt=(
                f"Respond as {archetype.title}. Focus on {archetype.scope}. "
                "Adapt your terminology to the user's echelon context. "
                "Vet ideas constructively with concerns, recommendations, and human-review cautions."
            ),
        )

    @property
    def definition(self) -> StaffRoleArchetype:
        """Backward-compat alias used by StaffCouncilService."""
        return self.archetype

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        echelon = _resolve_echelon(context)
        ectx = ECHELON_CONTEXT.get(echelon, ECHELON_CONTEXT[DEFAULT_ECHELON])
        arch = self.archetype

        focus_lines = "\n".join(f"- {item}" for item in arch.focus)

        osint_note = ""
        citations: list[str] = []
        structured = []
        trust = []
        if arch.osint_enabled:
            osint_response = build_osint_agent().run(input_text, context)
            citations.extend(osint_response.citations)
            osint_note = (
                "\nOSINT tie-in:\n"
                "- This role should call the OSINT source-evaluation workflow for public-source claims.\n"
                "- Treat trend/social evidence as low confidence unless corroborated.\n"
            )

        role_refs = _role_references(arch.role)
        all_refs = role_refs + arch.references_extra
        if all_refs:
            citations.extend(citation_titles(all_refs))
            structured.extend(structured_citations(all_refs))
            trust.extend(
                source_trust_markers(
                    all_refs,
                    notes_prefix="Verify current doctrine, training, and local applicability before action.",
                )
            )

        mos_section = ""
        if arch.mos_depth:
            mos_section = f"\nMOS-specific depth:\n{arch.mos_depth}\n"

        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = (
                "\nActive local operating context:\n"
                + "\n".join(f"- {line}" for line in active_context_lines)
                + "\n"
            )

        answer = _build_answer(arch, ectx, focus_lines, osint_note, mos_section, active_context_block)

        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citations,
            structured_citations=structured,
            source_trust=trust,
            confidence=Confidence.low,
            follow_up_questions=[
                "What decision are you asking the commander or staff to make?",
                "What is the timeline and next suspense?",
                "What source or local context should this role review?",
            ],
        )


# ---------------------------------------------------------------------------
# Answer builders — role-specific voice
# ---------------------------------------------------------------------------

def _build_answer(
    arch: StaffRoleArchetype,
    ectx: EchelonContext,
    focus_lines: str,
    osint_note: str,
    mos_section: str,
    active_context_block: str = "",
) -> str:
    role = arch.role
    title = f"{arch.title} ({ectx.scope_adjective})"

    if role == "xo":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Stay even-handed. Hear all sides, then cut to the governing point.\n"
            "- Fair does not mean soft. If the logic is weak, say so plainly.\n"
            "- If this does not have a clear owner, suspense, and command decision point, it is not ready.\n"
            "- If the plan depends on everyone remembering what they meant between drills, it will drift.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What is the actual decision that needs to be made now?\n"
            "- What will break first in execution, not in theory?\n"
            "- Which staff assumption is doing too much work?\n"
            "- What is the fairest and most workable cut through the competing preferences in the room?\n"
            "- What needs to be cut, simplified, or assigned immediately?\n\n"
            "Recommended next action:\n"
            "- Reduce this to a workable plan with owners, suspense dates, and one commander decision.\n"
            "- Push unresolved friction back to the responsible staff section before calling it ready."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "battle_captain":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- The watchboard is the fight. If it is stale, the command cell is stale.\n"
            "- I do not need every detail; I need what changed, what matters, and what escalates next.\n"
            "- If a trigger is not written down, the command post will discover it late.\n"
            "- Turnover quality is operational quality in smaller clothing.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What changed since the last huddle?\n"
            "- What is the next decision trigger and who gets called when it trips?\n"
            "- What watch item is being mistaken for a solved problem?\n"
            "- What will the relieving watch misunderstand first if we hand this over right now?\n\n"
            "Recommended next action:\n"
            "- Build a watchboard with current status, next suspense, next decision, and next escalation trigger.\n"
            "- Force turnover notes to capture what changed, what was elevated, and what the next watch must verify."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "opso":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Train to a standard. If there is no standard, you are only burning time.\n"
            "- Do not hand me decorative complexity and call it planning.\n"
            "- If it does not train a real standard, produce a needed output, or fit the available time,\n"
            "  it should not be on the schedule.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What MET, METL, or required skill does this event actually improve?\n"
            "- What products, rehearsals, or support requests are on the critical path?\n"
            "- What is training value, and what is just activity?\n"
            "- Which part of this is pretending to be ready because nobody wants the argument?\n\n"
            "Recommended next action:\n"
            "- Build the short training plan now: end state, products, coordination matrix, eval plan,\n"
            "  and AAR structure.\n"
            "- Strip out anything that cannot be prepared, resourced, and assessed inside the reserve timeline."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "s1":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Admin drift kills more plans than bad intent does.\n"
            "- If nobody owns the final route, suspense, and source check, the package is already late.\n"
            "- Reserve continuity fails quietly, then all at once, when notes are stale and handoffs are vague.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What admin action actually matters now, and what can stay in continuity tracking?\n"
            "- What source, routing chain, or suspense is still ambiguous?\n"
            "- What will be forgotten between drills if it is not written down today?\n"
            "- What travel-admin issue will hijack the next planning cycle if ignored?\n\n"
            "Recommended next action:\n"
            "- Publish one admin task tracker with owner, due date, source reference, and command touchpoint.\n"
            "- Run a pre-drill admin readiness check before dismissal so the next cycle does not start cold."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "s2":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- A weak estimate becomes dangerous the moment it starts sounding confident.\n"
            "- The staff needs one clear assessment, one key caveat, and one information gap that matters.\n"
            "- If the source picture is soft, brief the uncertainty instead of pretending it is settled.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What is actually known from public sources?\n"
            "- Which claim is still single-source, stale, or noisy?\n"
            "- What assumption would most change the commander's decision if it proves wrong?\n"
            "- What should be caveated instead of concluded?\n\n"
            "Recommended next action:\n"
            "- Reduce the estimate to corroborated facts, explicit assumptions, and one collection gap.\n"
            "- Keep OSINT in the sourced-public lane and kill anything that looks like guesswork."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "s4":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- If the support architecture is fuzzy, the event is still a hope, not a plan.\n"
            "- The item with the longest lead time owns the timeline whether the staff likes it or not.\n"
            "- Nice concepts usually die on transport, issue/turn-in, water, chow, or recovery time.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What absolutely cancels the event if unresolved?\n"
            "- Which support ask has the earliest no-later-than decision point?\n"
            "- What accountability or movement assumption is still doing too much work?\n"
            "- What should be cut now to protect supportability?\n\n"
            "Recommended next action:\n"
            "- Publish the minimum support package, longest lead-time suspense, and recovery timeline.\n"
            "- Force a yes, no, or not-yet from every support owner before calling the plan executable."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "s6":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Most reserve comm plans fail from confusion, not from exotic technical problems.\n"
            "- If reporting windows, fallback methods, and user access are not rehearsed,\n"
            "  the PACE plan is decoration.\n"
            "- Too many tools usually means nobody knows which one the commander actually cares about.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What information must move without fail, and in what time window?\n"
            "- What dies first: access, battery, permissions, user training, or report discipline?\n"
            "- What fallback method is simple enough to survive friction?\n\n"
            "Recommended next action:\n"
            "- Reduce the comm plan to one essential reporting flow, one fallback, and one missed-report action.\n"
            "- Solve CAC, PKI, access, and permissions problems before drill rather than during execution."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "sel":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Standards events fail when the unit treats sequence and accountability like details.\n"
            "- Marines can recover from friction faster than they can recover from looking unprepared in public.\n"
            "- If ceremony, customs, courtesies, or formation control matter here,\n"
            "  then rehearsal and ownership matter too.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What standard, custom, or formal process governs this event?\n"
            "- Who owns sequence control, accountability, and release criteria?\n"
            "- What would embarrass the unit if it went unverified?\n"
            "- What needs rehearsal instead of a verbal assumption?\n\n"
            "Recommended next action:\n"
            "- Write the troop-flow checklist, formation/transition matrix, and leader touchpoint plan now.\n"
            "- Verify ceremony and protocol questions against the governing reference before execution."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "surgeon":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- If casualty movement, qualified coverage, and stop-training criteria are vague,\n"
            "  the medical plan is not real.\n"
            "- Medical optimism is still risk, even when everyone means well.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What casualty scenario is most plausible enough to drive planning?\n"
            "- Who is qualified, equipped, and empowered to make the first hard call?\n"
            "- What TCCC knowledge and first-response expectations need refresh?\n"
            "- What 9-line, CASEVAC / MEDEVAC, and casualty-collection elements actually need rehearsal?\n\n"
            "Recommended next action:\n"
            "- Write the casualty scenarios, CASEVAC / MEDEVAC check, casualty collection logic,\n"
            "  coordination triggers, and stop-training criteria now.\n"
            "- Pause for qualified medical review before pretending the plan is executable."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "sja":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Legal review is useful early; late legal review only tells the commander which avoidable problem has "
            "already become expensive.\n"
            "- Treat this as issue-spotting, not legal advice.\n"
            "- Exercise plans still need guardrails: ROE/RUF training injects, safety investigation boundaries, "
            "claims, media release, detainee role-play, and ethics all need clean lanes.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What decision, authority, or legal review trigger is being assumed?\n"
            "- Does the exercise include investigations, claims, public release, or force escalation?\n"
            "- Where does the plan need SJA review before it is briefed as executable?\n\n"
            "Recommended next action:\n"
            "- Build a legal issue-spotter with ROE/RUF guardrails, investigation boundaries, and claims checks.\n"
            "- Separate training inject fiction from real-world legal authorities."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "pao":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Public posture is part of the plan, not garnish after the CONOP is done.\n"
            "- OPSEC, release authority, imagery, media access, and the exercise narrative need one coherent owner.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What can be said publicly, by whom, and at what release point?\n"
            "- What imagery, visitor, media, or community touchpoint creates OPSEC or reputation risk?\n"
            "- What message should the exercise reinforce, and what accidental message might it send?\n\n"
            "Recommended next action:\n"
            "- Build a public affairs/COMMSTRAT package covering release authority, OPSEC review, imagery handling, "
            "visitor/media choreography, themes and messages, and response-to-query lines."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "chaplain":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Religious support and morale planning are real readiness concerns.\n"
            "- Preserve confidential support boundaries.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- How will Marines access religious, moral, or confidential support during the event?\n"
            "- What casualty, memorial, family, or high-stress scenario needs RMT coordination?\n"
            "- What should be reported as readiness or morale context without exposing confidential communications?\n\n"
            "Recommended next action:\n"
            "- Build the religious support plan, RMT movement/support checklist, morale estimate, and "
            "confidentiality boundary note."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "provost":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- Access, force protection, traffic flow, visitor control, and simulated detainee/security injects need "
            "clear boundaries before they touch execution.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What access-control, traffic, or force-protection friction can delay the exercise?\n"
            "- Are any detainee, search, or security injects fictional and clearly bounded?\n"
            "- What installation or local security coordination must happen before movement?\n\n"
            "Recommended next action:\n"
            "- Build a security annex with access-control, movement-control, traffic/parking control, visitor "
            "processing, force-protection, and SJA/safety coordination points."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "ig":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- IG value comes from impartiality. Do not turn this lane into a shortcut for command-directed "
            "investigation or staff enforcement.\n"
            "- The useful IG contribution is inspection readiness, compliance trends, complaint "
            "boundaries, and systemic friction.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What readiness or compliance issue is systemic rather than merely inconvenient?\n"
            "- Is the staff trying to use IG language for something that belongs to command, SJA, or safety?\n"
            "- What inspection or inquiry boundary must be protected?\n\n"
            "Recommended next action:\n"
            "- Build an inspection readiness plan, inquiry boundary note, and readiness trend memo."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "g8":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- G-8 matters when the plan outruns the money, authorities, or execution window.\n"
            "- The useful output is a clear tradeoff frame the commander can actually use.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What resource assumption is carrying too much of the plan?\n"
            "- What can be funded, what can be absorbed, and what needs to be cut or deferred?\n"
            "- What resourcing decision belongs to command rather than staying buried in staff churn?\n\n"
            "Recommended next action:\n"
            "- Build a resource estimate, priority tradeoff brief, and resourcing decision point."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    if role == "g9":
        return (
            f"{title} staff-vetting perspective.\n\n"
            f"Scope: {arch.scope}\n\n"
            "My read:\n"
            "- External coordination fails when the staff treats continuity like a courtesy instead of a requirement.\n"
            "- Civil context helps only if it changes a real command problem.\n\n"
            f"Primary lenses:\n{focus_lines}\n\n"
            "Concerns to test:\n"
            "- What civil or partner factor actually changes the plan?\n"
            "- Who owns the next external touchpoint or continuity note?\n"
            "- What assumption about local familiarity or partner access is too casual?\n\n"
            "Recommended next action:\n"
            "- Narrow the civil picture to the handful of partner and continuity issues that can affect execution.\n"
            "- Write the revalidation point and the owner before drill ends."
            f"{active_context_block}{mos_section}{osint_note}"
        )

    # Fallback for any role not specifically voiced above
    return (
        f"{title} staff-vetting perspective.\n\n"
        f"Scope: {arch.scope}\n\n"
        f"Primary lenses:\n{focus_lines}\n\n"
        "Concerns to test:\n"
        "- Does the idea have a clear purpose, owner, timeline, and decision point?\n"
        "- What breaks during a reserve drill weekend with limited time and distributed personnel?\n"
        "- What official/public source should be checked before action?\n\n"
        "Recommended next action:\n"
        "- Turn the idea into a short staff estimate with assumptions, required coordination, risks, "
        "and a human reviewer."
        f"{active_context_block}{mos_section}{osint_note}"
    )


# ---------------------------------------------------------------------------
# Reference mapping
# ---------------------------------------------------------------------------

def _role_references(role: str) -> tuple[SourceRef, ...]:
    mapping: dict[str, tuple[SourceRef, ...]] = {
        "xo": S3_REFERENCES + STAFF_PRODUCT_REFERENCES,
        # chief: moved to standalone chief-of-staff
        "battle_captain": STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "opso": S3_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "s1": S1_REFERENCES,
        "s2": S2_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "s4": S4_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "s6": S6_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "sel": SEL_REFERENCES,
        "surgeon": MEDICAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "sja": LEGAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "pao": PAO_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        # safety: merged into orm-risk-management
        "chaplain": LEADERSHIP_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "provost": FORCE_PROTECTION_REFERENCES + LEGAL_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "ig": IG_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        # aviation: moved to standalone ace
        # lce: moved to standalone lce
        "g8": G8_REFERENCES + STAFF_PROCESS_REFERENCES + STAFF_PRODUCT_REFERENCES,
        "g9": G9_REFERENCES + STAFF_PRODUCT_REFERENCES,
    }
    return mapping.get(role, ())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def staff_agent_id(archetype: StaffRoleArchetype) -> str:
    return f"staff-{archetype.role}"


def build_staff_advisor_agents() -> list[StaffAdvisorAgent]:
    return [StaffAdvisorAgent(arch) for arch in ROLE_ARCHETYPES]


def list_staff_role_metadata() -> list[StaffRoleMetadata]:
    return [
        StaffRoleMetadata(
            agent_id=staff_agent_id(arch),
            echelon=StaffEchelon.battalion,  # default; adapts at runtime
            role=arch.role,
            name=arch.title,
            maturity="adapts to echelon",
            scope=arch.scope,
            osint_enabled=arch.osint_enabled,
        )
        for arch in ROLE_ARCHETYPES
    ]


# Legacy compatibility aliases
ROLE_DEFINITIONS = ROLE_ARCHETYPES
StaffRoleDefinition = StaffRoleArchetype
