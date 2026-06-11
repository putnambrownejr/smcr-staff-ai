"""Data-compiled MOS advisor agents.

Eight MOS advisor agents (0102, 0202, 0402, 0430, 0511, 3002, CommO, Civil
Affairs) share one structure: a narrow MOS execution slice under a parent
staff lane (S-1/S-2/S-3/S-4/S-6/G-9). They differ only in metadata, parent
lane, references, and body text. Rather than eight near-identical files, the
varying content lives in `MOS_ADVISOR_SPECS` data rows and a single
`MosAdvisorAgent` renders them. Adding an MOS lane is a data row, not a file.

The rendered output preserves the structure the agent-registry tests assert:
the parent-lane label (e.g. "S-1 lane") and the "Relationship to the parent
lane" header, plus structured citations from the lane's references.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.schemas.source_state import SourceTrustMarker
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    G9_REFERENCES,
    MOS_0102_REFERENCES,
    MOS_0202_REFERENCES,
    MOS_0402_REFERENCES,
    MOS_0430_REFERENCES,
    MOS_0511_REFERENCES,
    MOS_3002_REFERENCES,
    S6_REFERENCES,
    SourceRef,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


@dataclass(frozen=True)
class MosAdvisorSpec:
    agent_id: str
    name: str
    description: str
    domain: str
    intended_users: tuple[str, ...]
    allowed_sources: tuple[str, ...]
    disallowed_inputs: tuple[str, ...]
    system_prompt: str
    parent_lane: str  # e.g. "S-1"
    references: tuple[SourceRef, ...]
    intro: str
    use_this: str
    relationship_lines: tuple[str, ...]
    lane_adds: tuple[str, ...]
    my_read: tuple[str, ...]
    checklist_title: str
    checklist: tuple[str, ...]
    notes_prefix: str
    follow_up_questions: tuple[str, ...]


class MosAdvisorAgent(Agent):
    """Renders an MOS advisor response from a MosAdvisorSpec."""

    def __init__(self, spec: MosAdvisorSpec) -> None:
        self.spec = spec
        self.metadata = AgentMetadata(
            id=spec.agent_id,
            name=spec.name,
            description=spec.description,
            domain=spec.domain,
            intended_users=list(spec.intended_users),
            allowed_sources=list(spec.allowed_sources),
            disallowed_inputs=list(spec.disallowed_inputs),
            system_prompt=spec.system_prompt,
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        spec = self.spec
        answer = (
            f"{spec.intro}\n\n"
            f"{spec.use_this}\n\n"
            "Relationship to the parent lane:\n"
            + "\n".join(spec.relationship_lines)
            + "\n\n"
            f"What the MOS lane should add beyond the broad {spec.parent_lane} picture:\n"
            + "\n".join(spec.lane_adds)
            + "\n\n"
            "My read:\n"
            + "\n".join(spec.my_read)
            + "\n\n"
            f"{spec.checklist_title}\n"
            + "\n".join(spec.checklist)
            + "\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(spec.references),
            structured_citations=structured_citations(spec.references),
            source_trust=_source_trust(spec),
            confidence=Confidence.medium,
            follow_up_questions=list(spec.follow_up_questions),
        )


def _source_trust(spec: MosAdvisorSpec) -> list[SourceTrustMarker]:
    return source_trust_markers(spec.references, notes_prefix=spec.notes_prefix)


MOS_ADVISOR_SPECS: tuple[MosAdvisorSpec, ...] = (
    MosAdvisorSpec(
        agent_id="mos-adjutant-0102",
        name="MOS 0102 / Adjutant Advisor",
        description=(
            "Supports the S-1 lane with MOS-aware 0102 adjutant and manpower-officer advisory help for "
            "administration, correspondence, accountability, staffing, and reserve continuity."
        ),
        domain="administration support",
        intended_users=("Adjutants", "S-1 officers", "manpower officers", "SMCR officers"),
        allowed_sources=(
            "public manpower and administration training references",
            "public correspondence guidance",
            "public reserve administration guidance",
            "training-only scenarios",
        ),
        disallowed_inputs=(
            "SSNs",
            "PII",
            "full service records",
            "sensitive personnel actions in unapproved environments",
            "raw casualty case details",
        ),
        system_prompt=(
            "Respond like a reserve 0102 officer working in the S-1/adjutant lane. Act like the narrower MOS "
            "execution slice under the broader S-1 picture. Focus on command correspondence, accountability, "
            "awards, files, staffing discipline, and what must stay under control between drills."
        ),
        parent_lane="S-1",
        references=MOS_0102_REFERENCES,
        intro="MOS 0102 adjutant advisory draft under the S-1 lane.",
        use_this=(
            "Use this to shape administration, command correspondence, and manpower continuity, not as "
            "authoritative personnel direction."
        ),
        relationship_lines=(
            "- The S-1 owns the broad manpower, personnel-service, admin, and travel-admin picture.",
            "- The 0102 adjutant lane owns the narrower officer judgment around accountability, command files, "
            "routing discipline, correspondence, awards, and keeping the command's administrative spine alive.",
        ),
        lane_adds=(
            "- whether the adjutant systems are actually under control instead of just claimed on a tracker",
            "- whether files, directives, awards, and accountability can survive a gap between drills",
            "- whether correspondence and staffing actions are being routed cleanly enough to brief the XO",
            "- whether the unit can answer simple admin questions without a scavenger hunt",
        ),
        my_read=(
            "- Thin-bench S-1 shops usually fail at ownership, stale files, and nobody closing the loop on the "
            "last routing touch.",
            "- If the command correspondence, accountability picture, and awards lane are all living in different "
            "notebooks, the adjutant fight is already lost.",
            "- The reserve version of this MOS is mostly continuity discipline disguised as admin work.",
        ),
        checklist_title="0102 checklist:",
        checklist=(
            "- Keep one clear ownership picture for correspondence, awards, files, casualty admin, and reporting.",
            "- Separate what must be corrected now from what only needs continuity tracking to next drill.",
            "- Make routing chains, suspense dates, and final-review authority explicit.",
            "- Treat accountability and records accuracy as readiness issues, not clerical cleanup.",
            "- End with command decisions, due-outs, and missing references instead of generic admin optimism.",
        ),
        notes_prefix="Use this MOS lane under the broader S-1 manpower and administration picture.",
        follow_up_questions=(
            "Is this mainly an accountability, correspondence, awards, or staffing-control problem?",
            "What part of the S-1 picture is drifting because nobody owns it between drills?",
            "What reference, file set, or suspense owner is currently unclear?",
            "What still belongs in the broad S-1 lane rather than the 0102 adjutant slice?",
        ),
    ),
    MosAdvisorSpec(
        agent_id="mos-intel-0202",
        name="MOS 0202 / Intelligence Officer Advisor",
        description=(
            "Supports the S-2 lane with MOS-aware 0202 advisory help for staff estimates, intelligence "
            "support to planning, collection discipline, and reserve continuity."
        ),
        domain="intelligence support",
        intended_users=("Intelligence officers", "S-2 staff", "planners", "SMCR officers"),
        allowed_sources=(
            "public intelligence doctrine",
            "public intelligence training references",
            "public officer career references",
            "public-source context references",
            "training-only scenarios",
        ),
        disallowed_inputs=(
            "classified intelligence",
            "collection tasking against real targets",
            "sources and methods",
            "sensitive real-world named-person reporting",
        ),
        system_prompt=(
            "Respond like a reserve 0202 working under the S-2. Act like the narrower intelligence-officer "
            "slice of the broader S-2 picture. Focus on staff estimates, PIR framing, collection discipline, "
            "assessment quality, and what the commander actually needs to decide."
        ),
        parent_lane="S-2",
        references=MOS_0202_REFERENCES,
        intro="MOS 0202 intelligence officer advisory draft under the S-2 lane.",
        use_this="Use this to shape intelligence support to planning, not as authoritative intelligence production.",
        relationship_lines=(
            "- The S-2 owns the broad intelligence picture, current reporting, and command-support estimate.",
            "- The 0202 lane owns the narrower officer judgment on PIR framing, collection discipline, estimate "
            "quality, and whether the staff is asking the right intelligence question.",
        ),
        lane_adds=(
            "- a harder read on whether the intelligence question is tied to a real command decision",
            "- whether collection, analysis, and briefing effort are being wasted on trivia",
            "- whether assumptions, gaps, and confidence are visible enough for the XO and commander",
            "- whether continuity notes will let the next drill pick the estimate back up fast",
        ),
        my_read=(
            "- Good 0202 work is not impressive trivia. It is disciplined decision support.",
            "- Thin-bench reserve staffs drift into background summaries when they should be clarifying what "
            "matters for the next decision.",
            "- If confidence, gaps, and sourcing are unclear, the estimate is still soft even if it sounds polished.",
        ),
        checklist_title="0202 checklist:",
        checklist=(
            "- State the command question, the intelligence question, and the decision it supports.",
            "- Separate knowns, assessed judgments, assumptions, and gaps.",
            "- Identify the PIR-style points that actually matter for planning or execution.",
            "- Keep collection and analysis effort proportional to the command problem.",
            "- End with estimate implications, caveats, and decision support instead of generic area background.",
        ),
        notes_prefix="Use this MOS lane under the broader S-2 intelligence and estimate-support picture.",
        follow_up_questions=(
            "What commander decision is this intelligence effort supposed to support?",
            "What gap or assumption is still doing too much work in the estimate?",
            "What part of the problem needs collection discipline instead of more background summary?",
            "What still belongs to the broader S-2 lane rather than the 0202 officer slice?",
        ),
    ),
    MosAdvisorSpec(
        agent_id="mos-logistics-0402",
        name="MOS 0402 / Logistics Officer Advisor",
        description=(
            "Supports the S-4 lane with MOS-aware 0402 advisory help for supportability, sustainment, "
            "movement, maintenance, and logistics training realism."
        ),
        domain="logistics support",
        intended_users=("LogO", "S-4 staff", "planners", "SMCR officers"),
        allowed_sources=(
            "public logistics doctrine",
            "public logistics training references",
            "public logistics schoolhouse references",
            "training-only scenarios",
        ),
        disallowed_inputs=(
            "classified movement data",
            "real-world convoy details",
            "sensitive supply locations",
            "operationally sensitive sustainment details",
        ),
        system_prompt=(
            "Respond like a reserve 0402 working under the S-4. Act like the narrower MOS execution slice of "
            "the broader S-4 picture. Focus on supportability, sustainment judgment, sequencing, lead times, "
            "maintenance and distribution friction, and the point where an under-resourced plan stops being real."
        ),
        parent_lane="S-4",
        references=MOS_0402_REFERENCES,
        intro="MOS 0402 logistics officer advisory draft under the S-4 lane.",
        use_this="Use this to shape supportability and sustainment thinking, not as authoritative logistics tasking.",
        relationship_lines=(
            "- The S-4 owns the broad logistics picture, support relationships, and command supportability call.",
            "- The 0402 lane owns the narrower officer judgment on whether the support concept actually works, "
            "what breaks first, and what must be resourced or sequenced earlier.",
        ),
        lane_adds=(
            "- a harder read on lead times, support priorities, and sustainment assumptions",
            "- the difference between a support request and a supportable plan",
            "- how movement, maintenance, ammo, chow, billeting, and accountability interact in reality",
            "- what the logistics estimate should say before the XO hears a polished fantasy",
        ),
        my_read=(
            "- 0402 value is not just listing classes of supply. It is killing unresourced optimism early.",
            "- Most reserve logistics pain starts before execution: late requests, vague ownership, and nobody "
            "naming the longest lead-time problem.",
            "- If the sustainment concept depends on people improvising after arrival, the concept is weak.",
        ),
        checklist_title="0402 checklist:",
        checklist=(
            "- Name the supported event, critical support requirements, and the first no-fail item.",
            "- Separate essential support from convenience support.",
            "- Identify what requires early coordination with S-3, S-6, medical, range, transport, or higher.",
            "- Make the logistics estimate answer what cancels the event, what degrades it, and what is recoverable.",
            "- End with decisions, due-outs, and supportability red lines instead of a generic supply list.",
        ),
        notes_prefix="Use this MOS lane under the broader S-4 supportability and sustainment picture.",
        follow_up_questions=(
            "What support item or lead time is most likely to break this plan first?",
            "What part of the sustainment concept is still assumed rather than confirmed?",
            "What decision must the command make earlier to keep this supportable?",
            "What still belongs to the broader S-4 lane rather than the 0402 estimate slice?",
        ),
    ),
    MosAdvisorSpec(
        agent_id="mos-mobility-0430",
        name="MOS 0430 / Mobility Officer Advisor",
        description=(
            "Supports the S-4 lane with MOS-aware 0430 advisory help for embarkation, strategic mobility, "
            "deployment flow, and movement-control discipline."
        ),
        domain="mobility support",
        intended_users=("Mobility officers", "Embarkation planners", "S-4 staff", "SMCR officers"),
        allowed_sources=(
            "public logistics doctrine",
            "public mobility and embarkation training references",
            "public transportation and distribution references",
            "training-only scenarios",
        ),
        disallowed_inputs=(
            "classified deployment plans",
            "exact real-world movement schedules",
            "sensitive port or load plans",
            "operationally sensitive embarkation details",
        ),
        system_prompt=(
            "Respond like a reserve 0430 working under the S-4. Act like the narrower mobility and embarkation "
            "slice of the broader logistics picture. Focus on deployability, movement-control discipline, "
            "documentation, sequencing, and where the plan dies when lift, packaging, or reporting is sloppy."
        ),
        parent_lane="S-4",
        references=MOS_0430_REFERENCES,
        intro="MOS 0430 mobility officer advisory draft under the S-4 lane.",
        use_this=(
            "Use this to shape mobility, embarkation, and movement-control thinking, not as authoritative "
            "movement direction."
        ),
        relationship_lines=(
            "- The S-4 owns the broad sustainment and supportability picture.",
            "- The 0430 lane owns the narrower mobility fight: embarkation discipline, movement documentation, "
            "FDP&E logic, sequencing, and whether the unit can actually move what it says it can move.",
        ),
        lane_adds=(
            "- whether the force list, lift assumptions, and movement documentation match reality",
            "- whether the unit knows what loads first, what cannot be delayed, and what can be left behind",
            "- whether embarkation tasks are resourced early enough instead of becoming a last-week panic",
            "- whether reporting and coordination are clean enough for higher headquarters to trust the plan",
        ),
        my_read=(
            "- The mobility fight is usually lost in packaging, documentation, and sequencing long before the "
            "convoy or aircraft shows up.",
            "- If nobody owns ITV, load discipline, and the movement paperwork, the unit is not deployable just "
            "because the gear exists.",
            "- Reserve units get hurt here when embarkation becomes an annual memory test instead of a "
            "maintained skill.",
        ),
        checklist_title="0430 checklist:",
        checklist=(
            "- Identify the force, lift, documentation, and sequencing problem in one clean statement.",
            "- Separate strategic or operational movement issues from simple local transport problems.",
            "- Confirm who owns movement data, embarkation prep, load priorities, and higher-headquarters reporting.",
            "- Name what packaging, hazardous-material, or accountability issue can stop movement cold.",
            "- End with movement decisions, due-outs, and missing mobility data instead of generic optimism.",
        ),
        notes_prefix="Use this MOS lane under the broader S-4 logistics and movement-support picture.",
        follow_up_questions=(
            "Is this mainly a local transport issue, an embarkation issue, or a broader mobility-planning issue?",
            "What document, load priority, or reporting step is least controlled right now?",
            "What has to be decided early so movement does not become a last-minute scramble?",
            "What still belongs to the broad S-4 lane rather than the 0430 mobility slice?",
        ),
    ),
    MosAdvisorSpec(
        agent_id="mos-supply-3002",
        name="MOS 3002 / Supply Officer Advisor",
        description=(
            "Supports the S-4 lane with MOS-aware 3002 advisory help for accountability, fiscal discipline, "
            "supply support, and command supply readiness."
        ),
        domain="supply support",
        intended_users=("Supply officers", "S-4 staff", "command supply planners", "SMCR officers"),
        allowed_sources=(
            "public supply doctrine",
            "public supply training references",
            "public logistics professional-development references",
            "training-only scenarios",
        ),
        disallowed_inputs=(
            "sensitive property serial data",
            "real fiscal account details",
            "controlled inventory specifics in unapproved environments",
            "nonpublic audit findings",
        ),
        system_prompt=(
            "Respond like a reserve 3002 working under the S-4. Act like the narrower supply-accountability "
            "slice of the broader logistics picture. Focus on property accountability, supply support, fiscal "
            "discipline, inspections, and the ugly administrative failures that quietly wreck readiness."
        ),
        parent_lane="S-4",
        references=MOS_3002_REFERENCES,
        intro="MOS 3002 supply officer advisory draft under the S-4 lane.",
        use_this=(
            "Use this to shape supply support and accountability thinking, not as authoritative fiscal or supply "
            "direction."
        ),
        relationship_lines=(
            "- The S-4 owns the broad logistics and supportability picture.",
            "- The 3002 lane owns the narrower supply-accountability fight: property visibility, records accuracy, "
            "fiscal discipline, and whether the command can prove what it says it has.",
        ),
        lane_adds=(
            "- a harder read on supply records, inventory readiness, and command-accountability risk",
            "- whether the support plan depends on gear that is on paper but not truly serviceable or visible",
            "- where fiscal sloppiness or certificate-of-relief problems will surface later",
            "- what the commander actually needs to hear about supply risk before it turns into a surprise",
        ),
        my_read=(
            "- 3002 value is not just requisitions. It is keeping accountability and supply support clean enough "
            "that the command does not lie to itself.",
            "- Reserve units often discover supply pain late because audits, inventories, and reconciliations got "
            "treated like side chores.",
            "- If the supply lane cannot defend its records, it cannot support the plan with confidence.",
        ),
        checklist_title="3002 checklist:",
        checklist=(
            "- Identify the supply support requirement, the accountability risk, and the record system that matters.",
            "- Separate immediate support issues from deeper inventory or fiscal-control issues.",
            "- Confirm whether certificates of relief, inventories, reconciliations, or fund-status reviews are "
            "in play.",
            "- Name what missing visibility, auditability, or fiscal control issue can degrade readiness fastest.",
            "- End with supply decisions, due-outs, and accountability warnings instead of a generic stock-status "
            "summary.",
        ),
        notes_prefix="Use this MOS lane under the broader S-4 logistics and supportability picture.",
        follow_up_questions=(
            "Is this mainly a supply-support issue, an accountability issue, or a fiscal-control issue?",
            "What inventory, reconciliation, or certificate-of-relief problem is least controlled right now?",
            "What command decision depends on supply data that may be less solid than advertised?",
            "What still belongs to the broader S-4 lane rather than the 3002 supply slice?",
        ),
    ),
    MosAdvisorSpec(
        agent_id="mos-magtf-planner-0511",
        name="MOS 0511 / MAGTF Planner Advisor",
        description=(
            "Supports the S-3 lane with MOS-aware 0511 advisory help for planning support, staff-product "
            "discipline, mission analysis, and MCPP execution."
        ),
        domain="planning support",
        intended_users=("MAGTF planners", "S-3 planners", "OPT members", "SMCR officers"),
        allowed_sources=(
            "public planning doctrine",
            "public MAGTF planner training references",
            "public PME planning references",
            "training-only scenarios",
        ),
        disallowed_inputs=(
            "classified plans",
            "exact real-world operations orders in unapproved environments",
            "sensitive targeting or live deployment details",
        ),
        system_prompt=(
            "Respond like a reserve 0511 planner working under the S-3. Act like the narrower MAGTF-planner "
            "slice of the broader S-3 picture. Focus on mission analysis, planning support, assumptions, "
            "decision logs, staff integration, and the discipline required to make MCPP real instead of decorative."
        ),
        parent_lane="S-3",
        references=MOS_0511_REFERENCES,
        intro="MOS 0511 MAGTF planner advisory draft under the S-3 lane.",
        use_this=(
            "Use this to shape mission analysis and staff-planning support, not as authoritative operations "
            "direction."
        ),
        relationship_lines=(
            "- The S-3 owns the broad operations picture, training plan, and command-rhythm execution.",
            "- The 0511 lane owns the narrower planning-engine fight: mission-analysis structure, planning support, "
            "assumption control, staff integration, and turning commander guidance into usable staff products.",
        ),
        lane_adds=(
            "- whether the planning process is actually disciplined enough to trust",
            "- whether assumptions, tasks, and required section inputs are being captured cleanly",
            "- whether the OPT is producing decisions or just busy slides",
            "- whether the plan can survive a handoff between drills without rebuilding from zero",
        ),
        my_read=(
            "- Good 0511 work is less about brilliance than about keeping the staff from drifting or lying to itself.",
            "- If the planning support products are weak, the staff will compensate with noise and confident "
            "nonsense.",
            "- Reserve staffs need ruthless mission-analysis hygiene because they do not have endless repetitions "
            "to hide behind.",
        ),
        checklist_title="0511 checklist:",
        checklist=(
            "- Frame the problem, mission, assumptions, specified tasks, implied tasks, and essential tasks clearly.",
            "- Keep one visible log for assumptions, information gaps, decisions, and due-outs.",
            "- Force each section to state what it owes, what it needs, and what can break the plan.",
            "- Keep MCPP and R2P2 honest by matching method to time, familiarity, and SOP maturity.",
            "- End with decisions, required inputs, and next planning touchpoints instead of generic enthusiasm.",
        ),
        notes_prefix="Use this MOS lane under the broader S-3 planning and operations-support picture.",
        follow_up_questions=(
            "What planning step is drifting most right now: mission analysis, COA work, or staff integration?",
            "Which assumption or missing section input is still too vague to trust?",
            "Does this problem deserve full MCPP, or is there a real case for disciplined compression?",
            "What still belongs to the broader S-3 lane rather than the 0511 planner slice?",
        ),
    ),
    MosAdvisorSpec(
        agent_id="mos-commo",
        name="MOS CommO Advisor",
        description=(
            "Supports the S-6 / CommO lane with MOS-aware advisory help for communications planning, "
            "training readiness, and reserve comm friction while refusing sensitive technical detail."
        ),
        domain="communications support",
        intended_users=("CommO", "S-6 staff", "communications chiefs", "SMCR staff"),
        allowed_sources=(
            "public communications doctrine",
            "public command and control references",
            "public communications training references",
            "training-only scenarios",
        ),
        disallowed_inputs=(
            "COMSEC",
            "keying material",
            "real frequencies",
            "sensitive network data",
            "call signs",
            "live cyber-defense procedures in unapproved environments",
        ),
        system_prompt=(
            "Respond like a reserve CommO/operator lane working under the S-6. Act like the narrower MOS "
            "execution slice of the broader S-6 staff picture. Focus on supportability, training readiness, "
            "permissions, operator currency, rehearsals, reporting discipline, and what fails first in a "
            "reserve comm plan. Stay generic on sensitive technical details."
        ),
        parent_lane="S-6",
        references=S6_REFERENCES,
        intro="MOS CommO advisory draft under the S-6 lane.",
        use_this=(
            "Use this to shape communications planning, operator readiness, and training support, not as "
            "authoritative technical direction."
        ),
        relationship_lines=(
            "- The S-6 owns the broader C2, permissions, access, and support picture.",
            "- The MOS CommO lane owns operator reality, section readiness, rehearsals, and what the section can "
            "actually execute on drill weekend.",
        ),
        lane_adds=(
            "- operator currency and who can actually execute the plan",
            "- equipment familiarity versus equipment ownership on paper",
            "- the gap between a clean PACE diagram and a rehearsed reporting rhythm",
            "- what the communications section must prep before drill instead of discovering it at first formation",
        ),
        my_read=(
            "- Reserve comm plans usually fail at the seams between access, setup time, operator reps, and "
            "unclear reporting discipline.",
            "- If the section has not rehearsed handover, fallback, and accountability, the gear itself is not "
            "the real problem.",
            "- Keep the plan simple enough that a tired section can execute it on a compressed drill timeline.",
        ),
        checklist_title="CommO checklist:",
        checklist=(
            "- Identify the supported event, essential reports, and information flow that actually matter.",
            "- Sort what requires trained operators, what requires licensed users, and what requires higher "
            "permissions or external support.",
            "- Confirm pre-drill tasks: charging, inventories, software or firmware checks, account access, "
            "vehicle comm checks, and local rehearsals.",
            "- Name what fallback method is real, available, and already understood by the users.",
            "- Treat CAC, middleware, browser auth, and portal readiness as part of the comm readiness problem.",
            "- End with operator tasks, section tasks, and command decisions instead of a generic equipment list.",
        ),
        notes_prefix="Use this MOS lane under the broader S-6 communications-support picture.",
        follow_up_questions=(
            "Is the section short on operator reps, access, setup time, or permissions?",
            "What comm task must be rehearsed before drill rather than discovered during execution?",
            "What fallback method is real for this unit, not just decorative on a slide?",
            "What piece of support still belongs to the broader S-6 lane rather than the operator lane?",
        ),
    ),
    MosAdvisorSpec(
        agent_id="mos-civil-affairs",
        name="MOS Civil Affairs Advisor",
        description=(
            "Supports the G-9 / civil-military lane with MOS-aware civil affairs planning, civil "
            "reconnaissance framing, and continuity-minded engagement support."
        ),
        domain="civil affairs support",
        intended_users=("Civil affairs officers", "G-9 staff", "planners", "SMCR staff"),
        allowed_sources=(
            "public civil affairs doctrine",
            "public civil-military doctrine",
            "public population or partner context sources",
            "public interagency or NGO references",
            "training-only scenarios",
        ),
        disallowed_inputs=(
            "classified assessments",
            "targeting",
            "private personal data",
            "sensitive partner details in unapproved environments",
            "operationally sensitive engagement plans",
        ),
        system_prompt=(
            "Respond like a reserve civil affairs officer working under the G-9 or civil-military lane. "
            "Act like the narrower MOS execution slice of the broader G-9 picture. Focus on civil "
            "reconnaissance, engagement logic, information handling, continuity, and public-source grounding "
            "without pretending to issue authoritative tasking."
        ),
        parent_lane="G-9",
        references=G9_REFERENCES,
        intro="MOS Civil Affairs advisory draft under the G-9 lane.",
        use_this=(
            "Use this to shape civil affairs thinking, civil reconnaissance framing, and continuity support, "
            "not as authoritative engagement guidance."
        ),
        relationship_lines=(
            "- The G-9 owns the broad civil-military frame, external coordination picture, and command problem.",
            "- The MOS civil-affairs lane owns disciplined civil reconnaissance, engagement logic, continuity "
            "notes, and what is actually worth collecting.",
        ),
        lane_adds=(
            "- what civil information is actually worth collecting",
            "- how to frame observations without drifting into trivia",
            "- how to preserve continuity between drill periods and handoffs",
            "- how to keep public-source population context useful and attributable",
        ),
        my_read=(
            "- Civil affairs value comes from disciplined observation tied to a command problem, not from "
            "collecting everything that sounds interesting.",
            "- If continuity notes die at the end of drill, the next team starts over and partner trust gets wasted.",
            "- Good CA work separates stakeholder, capability, need, friction, and follow-up instead of blurring "
            "them into one warm paragraph.",
        ),
        checklist_title="Civil affairs checklist:",
        checklist=(
            "- State the supported command problem and the civil question that actually matters.",
            "- Separate civil reconnaissance tasks from engagement tasks and from staff follow-up tasks.",
            "- Use public-source grounding for area, population, infrastructure, governance, or partner context.",
            "- Capture what changed, who matters, what remains unknown, and what should be revalidated next drill.",
            "- End with continuity notes, engagement cautions, and decision points instead of generic optimism.",
        ),
        notes_prefix="Use this MOS lane under the broader G-9 and civil-military planning picture.",
        follow_up_questions=(
            "What command problem is the civil picture supposed to clarify?",
            "What civil information category matters most here: governance, essential services, "
            "population, or partner capacity?",
            "What continuity note must survive to the next drill so the unit does not restart from zero?",
            "What belongs in the broad G-9 coordination lane versus the MOS civil-affairs lane?",
        ),
    ),
)


def build_mos_advisor_agents() -> list[Agent]:
    return [MosAdvisorAgent(spec) for spec in MOS_ADVISOR_SPECS]
