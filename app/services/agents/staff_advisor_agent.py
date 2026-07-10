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

from pydantic import BaseModel

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, ScenarioOutputStatus
from app.schemas.scenario_handoff import G9ScenarioOutput, S2ScenarioOutput, S4ScenarioOutput, S6ScenarioOutput
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

_SCENARIO_SIGNALS = (
    "earthquake", "hurricane", "typhoon", "tsunami", "flood", "wildfire",
    "fhadr", "ha/dr", "disaster", "humanitarian",
    "exercise", "scenario", "vignette", "situation",
    "invasion", "insurgency", "conflict", "crisis", "coup",
    "partner nation", "host nation", "embassy", "country team",
    "meu", "jt", "jtf", "joint task force", "coalition",
    "noncombatant evacuation", "neo",
    "casualties", "displaced", "refugees",
)

_COUNTRY_SIGNALS = (
    "afghanistan", "australia", "bahrain", "canada", "china", "colombia",
    "djibouti", "egypt", "germany", "guam", "haiti", "honduras", "india",
    "indonesia", "iraq", "israel", "japan", "jordan", "kenya", "korea",
    "kuwait", "lebanon", "libya", "mexico", "morocco", "nato",
    "nicaragua", "niger", "nigeria", "norway", "okinawa",
    "pakistan", "panama", "peru", "philippines", "poland",
    "qatar", "romania", "russia", "saudi", "singapore", "somalia",
    "sudan", "syria", "taiwan", "thailand", "turkey", "ukraine",
    "venezuela", "vietnam", "yemen",
)


def _detect_scenario(input_text: str) -> bool:
    """Return True when the user input describes a specific scenario."""
    lowered = input_text.lower()
    has_scenario_signal = any(s in lowered for s in _SCENARIO_SIGNALS)
    has_country = any(c in lowered for c in _COUNTRY_SIGNALS)
    has_specifics = any(word in lowered for word in (
        "magnitude", "category", "casualties", "displaced", "population",
        "km", "miles", "destroyed", "damaged", "airport", "port", "road",
    ))
    # Scenario if: (scenario keyword + country) OR (scenario keyword + specific details)
    return has_scenario_signal and (has_country or has_specifics)


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
        mos_depth=(
            "Watch floor layout and roles: Battle Captain (overall watch authority), COP Manager "
            "(maintains common operational picture — analog mapboard + digital tracker), "
            "Intel Watch (threat updates, PIR tracking), Comms Net Control (radio/data link monitoring), "
            "S-1 Clerk (personnel status), Logistics NCO (supply/maintenance status), LNOs as needed.\n\n"
            "COP management: maintain both analog (mapboard with unit markers, phase lines, boundaries) "
            "and digital (C2 system) tracks. Three track categories: friendly (blue), enemy/threat (red), "
            "other (green — civilians, NGOs, neutral forces). Update cycle: continuous for friendly, "
            "as-received for threat, periodic for other.\n\n"
            "Information flow — SITREP format (6 sections): (1) DTG, (2) Unit, (3) Activity "
            "(what happened), (4) Effective (impact on operations), (5) Situation overview (current "
            "posture), (6) Request/remarks. SITREPs flow on scheduled battle rhythm.\n"
            "SALUTE report (spot report): Size, Activity, Location, Unit/uniform, Time, Equipment. "
            "SPOTREP: enemy contact — immediate transmission, no waiting for scheduled reporting.\n\n"
            "Watch turnover checklist: (1) Current friendly disposition and task org, (2) Current "
            "enemy situation and last known activity, (3) Significant events since last turnover, "
            "(4) Open/pending actions and suspenses, (5) Next scheduled events on the battle rhythm, "
            "(6) Commander's guidance and decision points, (7) Equipment/systems status.\n\n"
            "Incident reporting flow: initial report within 15 minutes (who/what/where/when + "
            "immediate actions taken) → follow-on report within 1 hour (amplifying details, "
            "response status) → AAR within 24-72 hours.\n\n"
            "Battle rhythm integration: the watch officer enforces the battle rhythm — update briefs, "
            "sync meetings, reports due — and escalates when a trigger or decision point is reached.\n\n"
            "Reserve / I&I constraints: limited manning means watch positions are often doubled up "
            "or rotated among a small team. Geographic dispersion means some watch functions run "
            "via phone/radio net rather than collocated. Drill-only activation means the watch floor "
            "must be stood up and torn down each drill — SOPs and checklists are critical to avoid "
            "losing continuity between drill weekends."
        ),
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
        scope="Administration, manpower, personnel readiness, and reserve admin systems",
        focus=(
            "rosters", "orders", "FitReps", "awards", "accountability",
            "correspondence", "Drill Manager", "MROWS", "MOL", "DTS",
        ),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "admin estimate", "admin task tracker", "routing matrix",
            "pre-drill admin readiness check", "drill-to-pay workflow",
        ),
        mos_depth=(
            "0102 Adjutant depth:\n"
            "- Admin system responsibilities: Drill Manager (IDT pay), MROWS (ADT/AT orders), "
            "MOL (self-service), DTS (travel), MCTFS/Unit Diary (status changes).\n"
            "- Baseline: 48 IDT + 14 days AT per year (MCO 1001R.1L w/CH-2, 7 Mar 2025).\n"
            "- MARADMIN 157/25: $750 IDT travel reimbursement cap.\n"
            "- Drill-to-pay: attendance captured → Drill Manager → pay run; errors delay entire cycle.\n"
            "- FitRep timeline: officer reporting periods, submission windows, RS/RO responsibilities.\n"
            "- Reserve friction points: asynchronous admin between drills, dual-status civilians, "
            "geographic dispersion, system fragmentation across 6+ platforms.\n"
            "- Whether adjutant systems are actually under control instead of just claimed on a tracker.\n"
            "- Whether files, directives, awards, and accountability can survive a gap between drills.\n"
            "- Whether correspondence and staffing actions route cleanly enough to brief the XO."
        ),
        references_extra=MOS_0102_REFERENCES,
    ),
    StaffRoleArchetype(
        role="s2",
        title="S-2 / G-2 / Intelligence",
        scope="Intelligence, public-source context, and estimate support",
        focus=(
            "IPB methodology", "collection management", "PIR framing",
            "source confidence", "information gaps", "all-source fusion",
        ),
        osint_enabled=True,
        products=(
            "intelligence estimate", "INTSUM", "collection plan",
            "IPB products (MCOO, doctrinal template, event template)",
        ),
        mos_depth=(
            "0202 Intelligence Officer depth:\n"
            "- IPB four-step methodology: define, describe, evaluate threat, determine COAs.\n"
            "- Collection management: translate PIR into specific collection requests with indicators.\n"
            "- All-source fusion: cross-reference HUMINT/SIGINT/OSINT into a single intelligence picture.\n"
            "- Whether the intelligence question is tied to a real command decision, not trivia.\n"
            "- Whether assumptions, gaps, and confidence are visible enough for the XO and commander.\n"
            "- Whether continuity notes will let the next drill pick the estimate back up fast.\n"
            "- OSINT methodology: frame requirement → acquire PAI/CAI → evaluate reliability → exploit → disseminate.\n"
            "- Force Design shift: organic sensors and reconnaissance increasingly decentralized to battalion."
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
        scope="Communications, C4I architecture, PACE planning, and information management",
        focus=(
            "PACE planning", "Annex K", "C2 architecture", "SATCOM",
            "MANET/mesh", "EMCON", "operator readiness",
        ),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "PACE plan by echelon", "Annex K (6 appendices)",
            "comm plan outline", "radio guard chart", "SATCOM request",
        ),
        mos_depth=(
            "0602 Communications Officer depth:\n"
            "- MAGTF C4I layers: enterprise (MCEN), tactical (radio nets), transport (SATCOM/relay).\n"
            "- Key radios: AN/PRC-117G (30-2000 MHz SATCOM/LOS), AN/PRC-160 (HF LPI/LPD), "
            "AN/PRC-158 (dual-channel 30-2500 MHz).\n"
            "- MANET/NOTM: Silvus StreamCaster 4400 for ad-hoc mesh at company and below.\n"
            "- MUOS for narrowband SATCOM; JENM for radio frequency planning.\n"
            "- PACE planning: Primary-Alternate-Contingency-Emergency for each reporting requirement.\n"
            "- Annex K structure: 6 appendices (signal, EMCON, spectrum, SATCOM, data, cyber).\n"
            "- Force Design 2030: mesh-first, EMCON-aware, reduced signature communications.\n"
            "- Whether the PACE plan is tied to actual reports, users, and decision points.\n"
            "- Whether operators, accounts, equipment, and permissions are ready before drill starts.\n"
            "- Whether rehearsals prove the reporting rhythm instead of only checking gear status."
        ),
        references_extra=S6_REFERENCES,
    ),
    StaffRoleArchetype(
        role="sel",
        title="SgtMaj / 1stSgt / Senior Enlisted Leader",
        scope="Standards, accountability, welfare, and discipline",
        focus=("standards", "welfare", "discipline", "accountability", "ceremony", "PME", "career"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "troop-flow checklist", "formation/transition matrix", "leader touchpoint plan",
            "PME tracking roster", "meritorious board prep", "SNCO development plan",
        ),
        mos_depth=(
            "Senior Enlisted Leader depth:\n\n"
            "ENLISTED PME GATES (MCO 1553.4B):\n"
            "- LCpl: Leading Marines (EPME3000, MarineNet distance) + LCpl Leadership & Ethics "
            "Seminar (341, one-day). Required after 3 of 9 drills and 6 months in grade.\n"
            "- Cpl: Corporals Course (C21, resident at regional PME academies). Complete "
            "Leading Marines first. Recommended before Sgt promotion.\n"
            "- Sgt: Sergeants School (T4M, resident) OR Sergeants Seminar (315) or Reserve "
            "Sergeants Course (CFF). Must complete Sergeant School DEP (EPME5000/T3W, "
            "MarineNet distance) before attending resident. Required before SSgt selection board.\n"
            "- SSgt: Staff NCO Career School (EPME6000/T5P, distance only). Required before "
            "GySgt selection board.\n"
            "- GySgt: SNCO Leadership School (31Q, resident) OR Seminar (31R). Must complete "
            "DEP EPME7000/T3X first. All GySgts must attend resident or equivalent.\n"
            "- MSgt/1stSgt: 1stSgt School (L64, resident) for 1stSgt selectees. MSgts attend "
            "annual SNCO seminars. GySgt PME must be complete.\n"
            "- SgtMaj/MGySgt: SNCO Symposium (MCSEA), Joint/SOLE PME (Cornerstone, EJPME II). "
            "No formal resident gate — selection board driven.\n\n"
            "COMPOSITE SCORE FACTORS (Cpl/Sgt promotion, MCO P1400.32):\n"
            "- PFT score (converted to points)\n"
            "- CFT score (converted to points)\n"
            "- Rifle score (service rifle, lookup table conversion)\n"
            "- Time in grade (weighted months)\n"
            "- Time in service (weighted months)\n"
            "- Proficiency marks (average from fitness reports)\n"
            "- Conduct marks (average from fitness reports)\n"
            "- Education points: up to 100 (15 per MCI, 10 per college course)\n"
            "- Special duty bonus: up to 100 (recruiter, DI, MSG, CEP)\n"
            "- Commands use composite scores to control promotion quotas. Marines become "
            "eligible when quarterly scores are posted.\n\n"
            "SNCO SELECTION BOARDS (SSgt and above):\n"
            "- Annual boards directed by Commandant's precept: select 'best and fully qualified.'\n"
            "- Key factors: fitness report quality and Relative Values (RVs), MOS credibility "
            "and breadth, PME completion (required PME must be done before board), "
            "awards/accomplishments, and absence of disciplinary issues.\n"
            "- Marines with resident PME are 'more highly qualified' than DEP-only.\n"
            "- No guarantee of selection; boards balance all factors.\n\n"
            "BOARD PREP (SEL should track for all eligible Marines):\n"
            "- OMPF audit: all awards, certs, duty history, and fitreps uploaded before board "
            "convenes. Missing material CANNOT be added after adjournment.\n"
            "- Master Brief Sheet (MBS): verify under PAWS — rifle, PFT, MCMAP scores, "
            "billet descriptions, rank, TIG. Submit corrections via IPAC (admin) or PEVS (fitrep).\n"
            "- Reserve Qualification Summary (RQS, NAVMC 10476): summarizes civilian skills and "
            "qualifications not in OMPF. Submit with board correspondence per convening MARADMIN.\n"
            "- Board correspondence: optional but useful. Letters, award certs, transcripts, "
            "endorsements sent to HQMC (MMPR-2) before deadline. Third-party endorsements "
            "must be signed by the Marine. Do NOT send original fitreps directly.\n\n"
            "RESERVE-SPECIFIC PME CHALLENGES:\n"
            "- Seat availability: nominations go through MSC or unit S-3 by deadline "
            "(typically T-45 before class report date). Quotas are limited.\n"
            "- SMCR units nominate via MSC. IRR Marines via MCIRSA (1-800-255-5082). "
            "IMA Marines through MARFOR training channels.\n"
            "- All distance DEPs (MarineNet) must be complete BEFORE scheduling resident school. "
            "Register early — failure to complete delays the slot.\n"
            "- Funding: MROWS orders with appropriate Reserve program codes. Marines on ADOS "
            "are unit-funded; commands often cancel ADOS during school period then resume after.\n"
            "- Duty-status waivers: required if not in full duty status. Obtained via MCU/CEME. "
            "Rare and require justification.\n"
            "- The USMC generally does NOT waive PME requirements. Missing PME by board date "
            "generally disqualifies the Marine for that board.\n"
            "- Best practice: treat reserve PME like an AT event — get orders, funds, and "
            "transportation arranged well ahead. Use unit AT to schedule travel.\n\n"
            "SNCO ACADEMY CURRICULUM:\n"
            "- Warfighting fundamentals: maneuver warfare, doctrine, operational planning.\n"
            "- Leadership & ethics: case studies, guided discussions, ethical decision-making.\n"
            "- Tactical skills: calling fires, land nav, tactical problem-solving.\n"
            "- Communication: writing orders, awards packages, briefs. Regular AARs.\n"
            "- Culminating field exercise/capstone event.\n"
            "- Regional academies: Quantico, Camp Pendleton, Lejeune, Okinawa, 29 Palms. "
            "Traveling Marines encouraged to use Quantico to free local slots.\n\n"
            "RESERVE SEL DUTIES:\n"
            "- Drill weekend accountability, liberty policy enforcement, new-join integration.\n"
            "- SGLI/page-11 verification, uniform inspection standards.\n"
            "- Coordination with I&I SEL for admin and readiness issues.\n"
            "- PME tracking: maintain a roster of all enlisted by rank, required PME, "
            "completion status, next board date, and composite score (for Cpl/Sgt).\n"
            "- Fitness report oversight: ensure fitreps are timely, ROs understand relative "
            "value impact, and comparison groups are appropriate.\n"
            "- UCMJ awareness: advise CO on NJP proceedings, witness statements, "
            "administrative actions (6105, page 11 entries).\n"
            "- Meritorious promotion boards: unit-level (Cpl/Sgt). Board prep: uniform/grooming, "
            "oral board (MOS knowledge, general military knowledge, current events, leadership "
            "scenarios), written test (MOS-specific), commander's recommendation."
        ),
        references_extra=SEL_REFERENCES,
    ),
    StaffRoleArchetype(
        role="surgeon",
        title="Surgeon / Medical / Doc",
        scope="Medical support, TCCC awareness, casualty planning, evacuation, and Navy reserve admin for corpsmen",
        focus=("casualty response", "CASEVAC", "medical risk", "TCCC", "medical readiness", "NOSC coordination"),
        magtf_lenses=(MagtfLens.gce, MagtfLens.lce),
        products=(
            "medical estimate", "CASEVAC / MEDEVAC check",
            "casualty collection logic", "coordination trigger list",
            "IMR status tracker", "Navy personnel orders request",
        ),
        mos_depth=(
            "Medical / Surgeon depth:\n\n"
            "Medical readiness:\n"
            "- IMR (Individual Medical Readiness) categories: fully medically ready, "
            "partially medically ready, not medically ready.\n"
            "- PHA (Periodic Health Assessment): annual requirement. Reserve Marines complete "
            "at drill or scheduled medical event. Delinquent PHA = not deployable.\n"
            "- Dental readiness: Class 1 (no treatment needed), Class 2 (treatment needed, "
            "not urgent — deployable), Class 3 (urgent treatment needed — NOT deployable), "
            "Class 4 (no dental exam on file — NOT deployable).\n"
            "- HIV testing: annual requirement for all servicemembers.\n"
            "- Immunizations: tracked in MRRS. Deployment-specific requirements vary by AOR.\n"
            "- DNA sample: one-time requirement, verified in MEDPROS.\n\n"
            "Navy personnel attached to Marine units (CRITICAL — different admin chain):\n"
            "- Corpsmen (HM), chaplains (RP), and other Navy rates attached to Marine commands "
            "are Navy reservists, not Marines. Their admin runs through the Navy Reserve, not USMC.\n"
            "- NOSC (Navy Operational Support Center): the Navy equivalent of I&I. Every Navy "
            "reservist is assigned to a NOSC for admin, pay, and orders processing.\n"
            "- Dual admin chain: the Marine unit is the gaining command (operational/training), "
            "but the NOSC is the supporting command (admin/orders/pay).\n"
            "- Orders processing: Navy reservists use NROWS (Navy Reserve Order Writing System), "
            "NOT MROWS. The gaining Marine unit writes the request letter, but the NOSC "
            "processes, funds, and issues the orders.\n"
            "- AT/ADT orders for Navy personnel: the Marine unit S-3/OpsO writes a letter of "
            "request to the NOSC specifying dates, location, funding source, and justification. "
            "NOSC submits in NROWS. Approval chain goes through CNRFC (Commander, Navy Reserve "
            "Forces Command), not MARFORRES.\n"
            "- ADSW/ADOS for Navy personnel: similar to Marine ADOS but processed through Navy "
            "channels. Different order types and funding categories.\n"
            "- Pay: Navy reservists are paid through Navy systems (MyPay/NSIPS), not Marine "
            "Corps pay systems. Pay issues route through the NOSC, not the Marine unit S-1.\n"
            "- Medical readiness: tracked in MRRS (Medical Readiness Reporting System) for Navy, "
            "not the same system Marines use. The gaining command sees readiness status but "
            "corrections route through the NOSC.\n"
            "- Common friction: Marine unit plans training, needs their doc — but orders take "
            "longer because they go through Navy channels. Start NROWS requests at T-60 minimum "
            "(vs T-45 for MROWS). Last-minute AT additions are much harder for Navy personnel.\n"
            "- NSIPS (Navy Standard Integrated Personnel System): Navy equivalent of MOL for "
            "service records, training, and admin.\n"
            "- The Marine unit surgeon/medical officer should maintain a tracker of all Navy "
            "personnel and their NOSC assignment, NROWS status, and readiness."
        ),
        references_extra=MEDICAL_REFERENCES,
    ),
    StaffRoleArchetype(
        role="sja",
        title="SJA / Legal",
        scope="Legal issue-spotting, ROE/RUF guardrails, military justice, admin law, and command legal routing",
        focus=(
            "military justice", "administrative law", "international/operational law",
            "legal assistance", "ROE/RUF", "issue spotting", "investigation boundaries",
        ),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "Legal issue-spotter", "ROE/RUF guardrails", "legal review trigger list",
            "NJP vs courts-martial routing", "mobilization legal readiness checklist",
        ),
        mos_depth=(
            "4402 Judge Advocate depth:\n"
            "- Six functional areas: military justice, international/operational law, administrative law, "
            "civil law, legal assistance, legal administration.\n"
            "- NJP: commanding officer authority under Article 15; accused right to demand trial; "
            "24-hr reflection; appeal within 5 days.\n"
            "- Courts-martial: summary (no right to counsel), special (BCD-authorized), "
            "general (Article 32 hearing required, felony-level).\n"
            "- Reserve-specific: UCMJ jurisdiction applies when on Title 10 orders or in IDT status; "
            "unsatisfactory participation separation under MCO P1900.16.\n"
            "- Mobilization legal readiness: powers of attorney, wills, SCRA protections, "
            "family care plans, employer notification.\n"
            "- What facts are missing before a lawyer can responsibly advise.\n"
            "- What command action should pause until the SJA or responsible counsel reviews it.\n"
            "- How to preserve clean routing, privilege awareness, and continuity between drills."
        ),
        references_extra=MOS_4402_REFERENCES,
    ),
    StaffRoleArchetype(
        role="pao",
        title="PAO / COMMSTRAT / Information",
        scope="Public affairs, COMMSTRAT, media posture, release authority, OPSEC coordination, and info effects",
        focus=(
            "COMMSTRAT", "public posture", "release authority",
            "OPSEC coordination", "narrative coherence",
            "generate/preserve/deny/project",
        ),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "Annex F (public affairs)", "COMMSTRAT plan", "release approval matrix",
            "response-to-query lines", "themes and messages",
            "media engagement plan", "community relations plan",
        ),
        mos_depth=(
            "COMMSTRAT / PAO depth:\n"
            "- Information environment functions: generate, preserve, deny, project (MCWP 8-10).\n"
            "- Annex F structure: media engagement, community relations, visual information, "
            "internal information.\n"
            "- PA vs COMMSTRAT: same function, evolving name — subordinate to the information staff.\n"
            "- Media engagement: accreditation, escort procedures, media rounds, embed rules.\n"
            "- Release authority: who can authorize public release at each echelon.\n"
            "- Integration: works with G-9/CMO for civil engagement and with S-2 for OPSEC review.\n"
            "- Whether themes and messages align with commander intent and higher guidance."
        ),
    ),
    # safety: merged into standalone orm-risk-management agent
    StaffRoleArchetype(
        role="chaplain",
        title="Chaplain / Religious Support",
        scope="Religious support, morale, ethical climate, confidential support, and Navy reserve admin for RPs",
        focus=("religious support", "morale", "confidentiality boundaries", "crisis response", "NOSC coordination"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "Religious support plan", "morale and welfare estimate", "confidentiality boundary note",
            "CACO notification checklist", "Navy personnel orders request",
        ),
        mos_depth=(
            "Chaplain / Religious Ministry Team depth:\n\n"
            "Religious Ministry Team (RMT):\n"
            "- The RMT consists of the chaplain and Religious Program Specialist (RP). "
            "Both are Navy personnel attached to the Marine unit.\n"
            "- MCO 1730.6: establishes command religious program requirements. Every command "
            "must provide for the free exercise of religion.\n"
            "- Privileged communication: under MRE 503, communications to a chaplain made as "
            "a formal act of religion or as a matter of conscience are privileged. The chaplain "
            "CANNOT be compelled to disclose — not by the CO, not by an IO, not by court-martial. "
            "This is absolute and non-waivable by the command.\n"
            "- The chaplain advises the CO on morale, welfare, and ethical climate but cannot "
            "share privileged content to do so.\n\n"
            "Crisis response:\n"
            "- CACO (Casualty Assistance Calls Officer): chaplain often accompanies CACO for "
            "notification. Notification must be in person, in uniform, during reasonable hours.\n"
            "- Suicide prevention: chaplain is part of the unit's suicide prevention program. "
            "DSTRESS line (1-877-476-7734) and Military OneSource (1-800-342-9647) are "
            "always-available resources.\n"
            "- Memorial affairs: chaplain leads memorial ceremonies. Format per unit SOP "
            "and Marine Corps tradition (rifle, boots, helmet, dog tags).\n"
            "- Critical incident stress: chaplain coordinates CISM (Critical Incident Stress "
            "Management) debriefings after significant events.\n\n"
            "Navy reserve admin (CRITICAL — same as corpsmen):\n"
            "- Chaplains and RPs are Navy reservists. Their orders, pay, and admin "
            "run through a NOSC (Navy Operational Support Center), not the Marine unit.\n"
            "- NOSC processes orders via NROWS (Navy Reserve Order Writing System), "
            "not MROWS. The Marine unit writes the request; the NOSC executes.\n"
            "- AT/ADT requests: Marine unit OpsO or S-1 sends a letter of request to "
            "the NOSC with dates, location, funding, and justification. "
            "NOSC submits in NROWS for CNRFC approval.\n"
            "- Start NROWS requests at T-60 minimum. Navy approval chain is slower "
            "than Marine MROWS — last-minute orders for chaplains/RPs are extremely "
            "difficult. Plan early.\n"
            "- Pay issues route through the NOSC, not the Marine S-1.\n"
            "- Medical/dental readiness tracked in MRRS, corrections through NOSC.\n"
            "- NSIPS for service records, not MOL.\n"
            "- The S-1 should maintain a tracker of all Navy personnel with NOSC "
            "assignment, NROWS status, and upcoming order requirements."
        ),
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
        focus=("resources", "prioritization", "funding risk", "fiscal execution", "reserve funding"),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "resource estimate", "funding risk note", "priority tradeoff brief",
            "resourcing decision point", "unfunded requirements list", "fiscal execution tracker",
        ),
        mos_depth=(
            "G-8 / Reserve Resources depth:\n\n"
            "RESERVE FUNDING CATEGORIES AND APPROPRIATIONS:\n"
            "- IDT (Inactive Duty Training): weekend drills, 4-hr drill periods, up to 48/year. "
            "Funded by RPMC (Reserve Personnel, Marine Corps, T/S 17-1108). "
            "Orders issued by unit CO/I&I detachment. No per diem. "
            "Travel reimbursement per JTR if >50 miles.\n"
            "- AT (Annual Training): mandatory yearly tour, 12-15 days active duty. "
            "Primary purpose: individual and unit readiness training. "
            "Funded by RPMC (17-1108). Travel and per diem from RPMC. "
            "Approved by HQMC or MARFORRES chain.\n"
            "- ADT (Active Duty for Training): tours beyond AT for schools, MTUs, "
            "pre-deployment training. Funded by RPMC (17-1108). "
            "Requires MARFORRES/G-3 or HQMC RA authorization.\n"
            "- ADOS-RC (Active Duty for Operational Support – Reserve Component): "
            "voluntary tours supporting reserve missions. Funded by RPMC (17-1108). "
            "Allocated by HQMC RA (Deputy CMC P&R to RA).\n"
            "- ADOS-AC (Active Duty for Operational Support – Active Component): "
            "voluntary tours supporting active component tasks. Funded by MPMC "
            "(Military Personnel, Marine Corps, T/S 17-1105). Falls under 'AC pay.' "
            "Allocated by HQMC RA via gaining commands.\n"
            "- MPA Orders: full-time active duty (AGR tours, mobilization, extended ADOS-AC). "
            "Funded by MPMC (17-1105). Approved by HQMC P&R or MARFORCOM.\n"
            "- ADOS day limits: 1,095 days in a 1,460-day rolling window. "
            "Extensions require HQMC approval.\n\n"
            "FISCAL YEAR EXECUTION TIMELINE:\n"
            "- 1 Oct: new FY begins. O&M and RPMC funds available for obligation. "
            "Commands receive initial allocations/allotments.\n"
            "- Oct-Dec: initial execution — book recurring requirements (training contracts, "
            "base ops, drill/AT orders). Quarterly reporting begins.\n"
            "- Mar-Apr: Mid-Year Review (MIDLIFE) — formal opportunity for units to report "
            "shortfalls and adjust spending plans. Commands submit UFRs to HQMC.\n"
            "- Jul: Congress enacts appropriation (if later than Oct); commands update plans.\n"
            "- Aug-Sep: year-end surge — finalize obligations, liquidate payments, accrue expenses, "
            "close out travel/contract orders. Reserve commands reconcile all transactions.\n"
            "- 30 Sep: all obligations must post to SABRS. Travel claims processed immediately after.\n"
            "- 1 Oct (next FY): funds expire. ULOs carry forward automatically. "
            "New FY budgets/apportionments issued.\n\n"
            "SABRS/DAI (Financial Systems):\n"
            "- SABRS (Standard Accounting, Budgeting, and Reporting System): legacy Marine Corps "
            "financial ledger since 1991. Transitioning to DAI.\n"
            "- DAI (Defense Agencies Initiative, Oracle EBS): centralized accounting, procurement, "
            "and interfaces. Integrates pay (MCTFS), travel (DTS), and procurement.\n"
            "- Key reports: Daily Transaction Report (review previous day's postings for correct "
            "amounts and financial codes), Error Transaction Report (failed edits/unmatched BEA), "
            "Status-of-Funds (trial balance, ULO reports — provided to reserve leadership weekly).\n"
            "- Error handling: per MCO 7300.21, errors must be corrected and reposted. "
            "Never delete error entries. Common issues: unmatched disbursements (UMDs), "
            "open commitments (NULOs). Escalate unresolved rejects to DFAS.\n"
            "- Marine Corps received clean audit in FY2023 after DAI implementation.\n\n"
            "UNFUNDED REQUIREMENTS (UFR) PROCESS:\n"
            "- Commanders identify and prioritize unfunded deficiencies, forward up chain.\n"
            "- Submission chain: unit budget officer → I&I/MSC G-8 → MARFORRES G-8 → HQMC P&R.\n"
            "- Assembled for mid-year review (spring) and again at year-end if needed.\n"
            "- HQMC allocates contingency or redistributed funds to highest-priority UFRs.\n"
            "- UFR entry format: ID, requirement/shortfall description, "
            "appropriation/fund/account (e.g., O&M MCR 17-1107 or RPMC 17-1108), "
            "cost ($), priority rank, justification/mission impact, requesting unit.\n"
            "- Major program shortfalls addressed via POM process; execution-year UFRs "
            "capture emergent needs.\n\n"
            "I&I COORDINATION (critical for reserve budget execution):\n"
            "- I&I staff hold the official allotment of RPMC/O&M funds and post SABRS/DAI entries.\n"
            "- Reserve budget officer defines requirements and schedules (IDT/AT calendars); "
            "I&I side obligates funds (orders, travel claims, purchase orders).\n"
            "- Training orders: reserve staff plans drills/AT; I&I processes MOL/DTS orders "
            "and travel authorizations using RPMC funds. Both verify point credit and pay.\n"
            "- Pay: I&I processes enlisted drill pay and officer stipends in MCTFS. "
            "Budget officer ensures RPMC drill pay funds are sufficient via monthly pay roster review.\n"
            "- Status-of-funds reports: I&I provides weekly to reserve leadership. "
            "Budget officer monitors execution against plan.\n"
            "- Escalation: fund errors/shortfalls go from I&I comptroller → I&I senior → "
            "MAGTF MSC G-8 → COMMARFORRES G-8 → HQMC P&R.\n\n"
            "KEY FINANCIAL CONTROLS:\n"
            "- Anti-Deficiency Act: cannot obligate beyond authorization. Violation is a "
            "criminal offense — report immediately.\n"
            "- Bona fide need rule: funds used in the year appropriated for needs arising "
            "in that year.\n"
            "- Purpose statute: funds used only for the appropriation's stated purpose.\n"
            "- Commanders are ultimately responsible for funds (MCO 7300.21).\n"
            "- Maintain audit trails: source documents for all obligating transactions. "
            "Retain contracts, travel vouchers, and supporting documentation.\n\n"
            "GOVERNMENT PURCHASE CARD (GPC):\n"
            "- Micro-purchase threshold: $3,500 for supplies, $2,500 for services.\n"
            "- Requires appointed Agency Program Coordinator (APC) and cardholder training.\n"
            "- Monthly reconciliation required in the bank's electronic access system.\n\n"
            "RESERVE-SPECIFIC FUNDING FRICTION:\n"
            "- Travel is the largest discretionary cost — Marines driving 100+ miles to drill.\n"
            "- AT funding must be locked 90 days out or risk losing billets.\n"
            "- ADOS-AC competes with active component requirements; ADOS-RC is reserve-controlled.\n"
            "- Equipment shortfalls often require cross-leveling from sister units.\n"
            "- Range/facility costs must be budgeted quarterly.\n"
            "- PME travel for reserves (schools): use MROWS with appropriate Reserve program codes. "
            "Marines on ADOS are unit-funded; commands sometimes cancel ADOS during school then resume.\n"
            "- Navy personnel (corpsmen/chaplains): their orders and pay go through NOSC/NROWS, "
            "not Marine systems. Budget officer must coordinate with NOSC for funding."
        ),
        references_extra=G8_REFERENCES,
    ),
    StaffRoleArchetype(
        role="g9",
        title="G-9 / Civil-Military",
        scope="Civil-military operations, civil affairs, community context, and partner coordination",
        focus=(
            "civil estimate", "CPB", "ASCOPE/PMESII", "Annex G",
            "civil reconnaissance", "external coordination", "transition planning",
        ),
        magtf_lenses=(MagtfLens.ce_c2,),
        products=(
            "civil estimate", "Annex G (civil-military operations)",
            "civil preparation of the battlespace (CPB)", "civil information requirements (CIR)",
            "partner coordination plan", "transition plan",
        ),
        mos_depth=(
            "G-9 / CMO depth:\n"
            "- CPB parallels IPB for the civil dimension: ASCOPE (areas, structures, capabilities, "
            "organizations, people, events) crossed with PMESII.\n"
            "- Civil estimate feeds Annex G — includes civil situation, impact on operations, "
            "requirements, resources, and recommendations.\n"
            "- CIR format: civil information requirement with indicators, collection means, "
            "and responsible section.\n"
            "- Echelon differences: battalion has no organic G-9; regiment may have a civil affairs "
            "detachment; MEF has a full G-9 section.\n"
            "- Information environment integration: generate/preserve/deny/project (MCWP 8-10) — "
            "CMO supports the information function through civil engagement.\n"
            "- Targeting integration: civil considerations shape no-strike lists and collateral damage.\n"
            "- Transition planning: conditions-based handoff to host nation or follow-on force.\n"
            "\n"
            "Interagency coordination (post-2025 USAID dissolution):\n"
            "- USAID is operationally defunct. All civilian humanitarian/development functions "
            "now fall under the Department of State.\n"
            "- New State structure: Under Secretary for Foreign Assistance & Humanitarian Affairs "
            '("F") oversees Bureau for Humanitarian Assistance, Bureau of Global Health Security '
            "& Diplomacy, PRM, DRL, and Bureau of Disaster and Humanitarian Response (DHR).\n"
            "- Country Team framework remains the primary civ-mil coordination mechanism at each "
            "embassy. State officials now fill the role USAID personnel held.\n"
            "- USAID's Office of Civilian-Military Coordination (CMC), which embedded officers "
            "in each combatant command, is transitioning to State.\n"
            "- DART teams were shelved (BHA cut from ~1,300 to ~50 staff). State's "
            "DHR has rebuilt DART-equivalent capability.\n"
            "- DoD Civil Affairs units bear a larger disaster response role in the interim.\n"
            "- JP 3-29 and JP 3-57 still reference USAID/OFDA as lead — pending doctrinal update. "
            "Substitute State's humanitarian bureau wherever USAID appears.\n"
            "- FY2026 humanitarian budget cut ~two-thirds (from ~$9.9B to ~$2.5B) — "
            "factor degraded civilian capacity into FHADR planning.\n"
            "- Regional development now managed by State geographic bureaus (AFR, EAP, EUR, NEA, WHA) "
            "not dedicated USAID regional offices.\n"
            "- Food for Peace (Title II) transferred to USDA, not State.\n"
            "\n"
            "For joint operations, multinational coordination, and broader interagency mechanics "
            "(command relationships, liaison, comms interop, agreements), see docs/interagency_reference.md."
        ),
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
                "Vet ideas constructively with concerns, recommendations, and human-review cautions.\n\n"
                "SCENARIO MODE: If the user provides a specific scenario (country, event type, forces, "
                "timeline, or situation details), apply your framework TO that scenario and produce a "
                "structured assessment. Do not return the framework description — return your analysis "
                "of the situation using the framework."
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

        population = _build_answer(
            arch, ectx, focus_lines, osint_note, mos_section,
            active_context_block, input_text, context,
            self.metadata.system_prompt or "",
        )

        return self._response(
            answer=population.answer,
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
            scenario_output=population.scenario_output,
            scenario_output_status=population.status,
            additional_warnings=population.warnings,
            allow_warning_override=bool(
                context.external_processing_approval
                and context.external_processing_approval.acknowledged
            ),
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
    input_text: str = "",
    context: AgentContext | None = None,
    system_prompt: str = "",
) -> ScenarioPopulation:
    role = arch.role
    title = f"{arch.title} ({ectx.scope_adjective})"

    # --- Scenario-mode: produce an assessment template + structured output ---
    if input_text and _detect_scenario(input_text):
        scenario_result = _build_scenario_answer(
            role, title, focus_lines, osint_note, mos_section,
            active_context_block, input_text, context, system_prompt,
        )
        if scenario_result is not None:
            return scenario_result

    # Non-scenario: return text only, no structured output
    text = _build_answer_text(arch, role, title, ectx, focus_lines, osint_note, mos_section, active_context_block)
    return ScenarioPopulation(answer=text)


def _build_answer_text(
    arch: StaffRoleArchetype,
    role: str,
    title: str,
    ectx: EchelonContext,
    focus_lines: str,
    osint_note: str,
    mos_section: str,
    active_context_block: str = "",
) -> str:
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
# Scenario-mode answer builders
# ---------------------------------------------------------------------------

_LLM_UNAVAILABLE_NOTICE = (
    "\n\n---\n"
    "NOTE: This is a local deterministic template. Configure external processing "
    "and approve its preview to populate the assessment automatically."
)

_LLM_LOCAL_ONLY_NOTICE = (
    "\n\n---\n"
    "NOTE: You selected the local-only path. No scenario content was sent to an external provider."
)

_LLM_FAILURE_NOTICE = (
    "\n\n---\n"
    "NOTE: The approved external request did not return usable content. "
    "The local deterministic template is shown instead."
)


@dataclass(frozen=True)
class ScenarioPopulation:
    answer: str
    scenario_output: dict[str, object] | None = None
    status: ScenarioOutputStatus = ScenarioOutputStatus.not_applicable
    warnings: list[str] | None = None


def _try_llm_populate(
    template: str,
    input_text: str,
    system_prompt: str,
    output_model: type[BaseModel],
    expected_role: str,
    context: AgentContext | None = None,
) -> ScenarioPopulation:
    """Populate a scenario template only after the outbound preview is approved."""
    from app.services.agents.scenario_envelope import (
        ScenarioEnvelopeParser,
        ScenarioEnvelopeValidationError,
        build_envelope_template,
    )
    from app.services.llm_client import ScenarioGenerationStatus, generate_scenario_response

    active_context = context or AgentContext()
    outbound_template = build_envelope_template(template, output_model)
    result = generate_scenario_response(
        system_prompt,
        outbound_template,
        input_text,
        approval=active_context.external_processing_approval,
        preview_only=active_context.external_processing_preview_only,
        user_key=active_context.user_key,
        scope_label=active_context.external_processing_scope_label or "agent:scenario",
        expected_call_count=active_context.external_processing_expected_call_count,
        approval_digest_override=active_context.external_processing_approval_digest_override,
    )
    if result.content is not None:
        try:
            parsed = ScenarioEnvelopeParser().parse(
                result.content,
                output_model=output_model,
                expected_role=expected_role,
            )
        except ScenarioEnvelopeValidationError as exc:
            fallback_answer = exc.answer or (template + _LLM_FAILURE_NOTICE)
            return ScenarioPopulation(
                answer=fallback_answer,
                status=ScenarioOutputStatus.invalid,
                warnings=[f"Structured scenario handoff unavailable: {exc.reason}"],
            )
        return ScenarioPopulation(
            answer=parsed.answer,
            scenario_output=parsed.scenario_output,
            status=ScenarioOutputStatus.validated,
        )
    if result.status is ScenarioGenerationStatus.local_only:
        return ScenarioPopulation(
            answer=template + _LLM_LOCAL_ONLY_NOTICE,
            status=ScenarioOutputStatus.template_only,
        )
    if result.status is ScenarioGenerationStatus.failed:
        return ScenarioPopulation(
            answer=template + _LLM_FAILURE_NOTICE,
            status=ScenarioOutputStatus.invalid,
            warnings=["Approved external processing failed; no structured handoff was produced."],
        )
    return ScenarioPopulation(
        answer=template + _LLM_UNAVAILABLE_NOTICE,
        status=ScenarioOutputStatus.template_only,
    )


def _prior_assessment_context(context: AgentContext | None) -> str:
    """Build a text block summarizing prior assessments for scenario prompts."""
    if context is None or not context.prior_assessments:
        return ""
    lines = ["\n\nPRIOR STAFF ASSESSMENTS (from upstream agents):"]
    for role_key, assessment in context.prior_assessments.items():
        lines.append(f"\n--- {role_key.upper()} ---")
        if isinstance(assessment, dict):
            for field, value in assessment.items():
                if field == "role":
                    continue
                if value and value != [] and value != {}:
                    lines.append(f"  {field}: {value}")
        else:
            lines.append(f"  {assessment}")
    return "\n".join(lines)


def _build_scenario_answer(
    role: str,
    title: str,
    focus_lines: str,
    osint_note: str,
    mos_section: str,
    active_context_block: str,
    input_text: str,
    context: AgentContext | None = None,
    system_prompt: str = "",
) -> ScenarioPopulation | None:
    """Return a scenario population result, or None to fall through."""

    prior_context = _prior_assessment_context(context)

    scenario_header = (
        f"{title} — SCENARIO ASSESSMENT\n\n"
        "A specific scenario was detected. Use this structured assessment framework "
        "to analyze the situation. Each section targets a specific staff product area — "
        "work through them using the scenario details provided.\n\n"
    )

    if role == "g9":
        text = (
            f"{scenario_header}"
            "CIVIL ESTIMATE (scenario-specific):\n\n"
            "1. CIVIL SITUATION:\n"
            "   - Area: Identify the operating environment from the scenario — geography, urban/rural mix, "
            "access routes, and key civil terrain\n"
            "   - Population: Describe the affected population — size, displacement status, demographics, "
            "and immediate needs\n"
            "   - Infrastructure: Assess damaged or degraded infrastructure — ports, airports, roads, "
            "hospitals, water/power systems\n"
            "   - Governance: Identify the host nation governance posture and primary counterpart "
            "for civil-military coordination\n\n"
            "2. ASCOPE ANALYSIS (apply to this scenario):\n"
            "   - Areas: Identify key civil terrain — population centers, displacement routes, aid distribution "
            "points, protected sites\n"
            "   - Structures: Assess status of hospitals, schools, government buildings, ports, airports\n"
            "   - Capabilities: Evaluate host nation response capacity, NGO presence, existing coordination "
            "mechanisms already in place\n"
            "   - Organizations: Identify which NGOs, IOs, and government agencies are operating or expected "
            "in this scenario\n"
            "   - People: Identify key leaders, vulnerable populations, and cultural considerations that "
            "affect operations\n"
            "   - Events: Note upcoming events that affect operations — elections, religious observances, "
            "market days, seasonal factors\n\n"
            "3. INTERAGENCY COORDINATION:\n"
            "   - US Embassy / Country Team: Identify the coordination node and current posture\n"
            "   - DoS/DHR: Determine whether a DART or equivalent is deployed and which State bureau is lead\n"
            "   - UN/OCHA: Determine whether clusters are activated and which ones are relevant to this scenario\n"
            "   - NGO landscape: Identify who is operating, who may resist military coordination, and why\n\n"
            "4. IMPACT ON MILITARY OPERATIONS:\n"
            "   - Identify civil factors that constrain or enable the military mission\n"
            "   - Assess no-strike / protected site considerations\n"
            "   - Recommend transition conditions to set early\n\n"
            "5. CMO RECOMMENDATIONS:\n"
            "   - Recommend priority civil-military coordination actions for this scenario\n"
            "   - Identify liaison requirements — who needs an LNO where\n"
            "   - List civil information requirements (CIR) to feed the civil estimate\n"
            "   - Identify the civil assumption that would most change the plan if wrong\n"
            f"{active_context_block}{mos_section}{osint_note}{prior_context}"
        )
        return _try_llm_populate(text, input_text, system_prompt, G9ScenarioOutput, "g9", context)

    if role == "s2":
        text = (
            f"{scenario_header}"
            "INTELLIGENCE ESTIMATE (scenario-specific):\n\n"
            "1. AREA OF OPERATIONS:\n"
            "   - Define the AO and area of interest based on the scenario geography\n"
            "   - Assess key terrain and weather effects on operations\n"
            "   - Evaluate infrastructure status — LOCs, ports, airfields, bridges\n\n"
            "2. THREAT / ADVERSARY ASSESSMENT:\n"
            "   - Identify threat actors relevant to this scenario — state, non-state, criminal, spoiler\n"
            "   - Assess threat disposition, capabilities, and likely intentions\n"
            "   - Develop threat COAs: most likely and most dangerous\n"
            "   - Note historical pattern of threat activity in this area\n\n"
            "3. CIVIL CONSIDERATIONS (IPB Step 2):\n"
            "   - Assess population demographics, displacement patterns, and attitudes toward US forces\n"
            "   - Evaluate the media environment and information threats\n"
            "   - Identify political dynamics that affect the mission\n\n"
            "4. INTELLIGENCE GAPS:\n"
            "   - Identify what the commander does NOT know but needs for decisions\n"
            "   - Develop Priority Intelligence Requirements (PIR) for this scenario\n"
            "   - Recommend collection means — OSINT, liaison, organic sensors\n\n"
            "5. ASSESSMENT:\n"
            "   - State the bottom line: what the commander must understand about this environment\n"
            "   - List key assumptions and their confidence level\n"
            "   - Describe what changes if the most dangerous threat COA materializes\n"
            f"{active_context_block}{mos_section}{osint_note}{prior_context}"
        )
        return _try_llm_populate(text, input_text, system_prompt, S2ScenarioOutput, "s2", context)

    if role == "s4":
        text = (
            f"{scenario_header}"
            "LOGISTICS ESTIMATE (scenario-specific):\n\n"
            "1. SITUATION:\n"
            "   - Assess the logistics environment — distances, infrastructure condition, climate effects\n"
            "   - Determine what sustainment is available in theater vs. requires deployment\n\n"
            "2. SUPPORT REQUIREMENTS:\n"
            "   - Class I (rations): Develop feeding plan for the force size and expected duration\n"
            "   - Class III (fuel): Estimate consumption rates and identify resupply sources\n"
            "   - Class V (ammo): Assess requirements if security/force protection role applies\n"
            "   - Class VIII (medical): Develop CASEVAC plan, identify nearest MTF, assess medical logistics\n"
            "   - Transportation: Determine lift requirements and develop movement plan\n\n"
            "3. SUPPORTABILITY ASSESSMENT:\n"
            "   - Determine what is supportable with current resources\n"
            "   - Identify what requires host nation support, cross-service support, or contract\n"
            "   - Identify the longest lead-time item and its decision point\n\n"
            "4. LOGISTICS RECOMMENDATIONS:\n"
            "   - Recommend priority support actions for this scenario\n"
            "   - Identify support agreements needed — CSSA, ACSA, host nation\n"
            "   - Identify the logistics assumption that breaks the plan if wrong\n"
            f"{active_context_block}{mos_section}{osint_note}{prior_context}"
        )
        return _try_llm_populate(text, input_text, system_prompt, S4ScenarioOutput, "s4", context)

    if role == "s6":
        text = (
            f"{scenario_header}"
            "COMMUNICATIONS ASSESSMENT (scenario-specific):\n\n"
            "1. COMMUNICATIONS ENVIRONMENT:\n"
            "   - Assess available comms infrastructure in the AO\n"
            "   - Identify joint/coalition/interagency comms requirements for this scenario\n"
            "   - Note spectrum management considerations and host nation restrictions\n\n"
            "2. PACE PLAN (for this scenario):\n"
            "   - Primary: Recommend primary comms method based on scenario environment and partners\n"
            "   - Alternate: Recommend alternate comms path\n"
            "   - Contingency: Recommend contingency comms method\n"
            "   - Emergency: Recommend emergency comms fallback\n\n"
            "3. INTEROPERABILITY ISSUES:\n"
            "   - Identify comms gaps with joint/coalition/interagency partners in this scenario\n"
            "   - Assess COMSEC sharing limitations\n"
            "   - Determine data link and network integration requirements\n\n"
            "4. RECOMMENDATIONS:\n"
            "   - Recommend priority comms actions before deployment\n"
            "   - Identify liaison comms requirements\n"
            "   - Identify the comms assumption most likely to fail first\n"
            f"{active_context_block}{mos_section}{osint_note}{prior_context}"
        )
        return _try_llm_populate(text, input_text, system_prompt, S6ScenarioOutput, "s6", context)

    # Roles without a specific scenario template fall through to framework mode
    return None


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
