from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S1_REFERENCES,
    SEL_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)

_CHECKIN_REFERENCES = (*S1_REFERENCES, *SEL_REFERENCES)


class CheckinAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="unit-checkin",
            name="Unit Check-In / Reporting Advisor",
            description=(
                "Step-by-step guide for checking in to a new USMC reserve unit — admin paperwork, "
                "system enrollments, formal reporting protocol, gear issue, and first-drill survival. "
                "Covers officer and enlisted, lateral moves, and I&I coordination."
            ),
            domain="unit check-in and reporting",
            intended_users=[
                "SMCR officers",
                "SMCR enlisted",
                "new joins",
                "lateral movers",
                "I&I staff",
                "S-1",
            ],
            allowed_sources=[
                "public Marine Corps admin orders and directives",
                "public uniform and protocol references",
                "local unit check-in guidance",
            ],
            disallowed_inputs=[
                "classified information",
                "CUI",
                "PII beyond what's needed for the checklist",
            ],
            system_prompt=(
                "You are a practical check-in advisor for Marines reporting to a new SMCR unit. "
                "Walk them through every step — paperwork, admin systems, formal reporting, gear, "
                "and the social reality of being the new person. Be specific enough that a Marine "
                "who has never done this before can execute without asking 20 questions. Cover both "
                "the admin grind and the protocol/customs piece."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = (
                "Active local operating context:\n"
                + "\n".join(f"- {line}" for line in active_context_lines)
                + "\n\n"
            )

        lowered = input_text.lower()
        is_officer = any(w in lowered for w in ("officer", "lt", "capt", "maj", "col", "mos 0"))
        is_enlisted = any(w in lowered for w in ("enlisted", "lcpl", "cpl", "sgt", "ssgt", "gysgt"))
        is_lateral = any(w in lowered for w in ("lateral", "transfer", "pcs", "new unit", "switching"))

        role_note = ""
        if is_officer:
            role_note = (
                "Officer-specific notes:\n"
                "- You will formally report to the CO. Alphas required unless told otherwise.\n"
                "- Prepare a 60-second introduction: name, rank, MOS, where you're coming from, "
                "what you bring to the unit.\n"
                "- The CO may ask about your professional goals and how you see yourself contributing.\n"
                "- You may also report to the XO and your immediate supervisor (OIC/section head).\n"
                "- Request your reporting senior's expectations for your first FitRep period.\n\n"
            )
        elif is_enlisted:
            role_note = (
                "Enlisted-specific notes:\n"
                "- You will report to your section SNCO or platoon sergeant first, "
                "then be presented to the 1stSgt/SgtMaj.\n"
                "- The 1stSgt may bring you before the CO or the CO may see new joins at formation.\n"
                "- Know your MOS, last duty station, and be ready to answer questions about your "
                "training and qualifications.\n\n"
            )

        lateral_note = ""
        if is_lateral:
            lateral_note = (
                "Lateral move / transfer notes:\n"
                "- Ensure your losing unit has completed your checkout and service record transfer.\n"
                "- OMPF and SRB should be current — missing documents from your old unit will haunt you.\n"
                "- If transferring between MSCs (4th MarDiv → 4th MLG, etc.), expect extra admin lag.\n"
                "- Your drill points and retirement year may need manual verification after transfer.\n\n"
            )

        answer = (
            "Unit check-in advisory.\n\n"
            f"{active_context_block}"
            "PHASE 1 — BEFORE YOUR FIRST DRILL (T-30 to T-7)\n\n"
            "Administrative preparation:\n"
            "- Contact the unit S-1 or I&I admin chief. Get the check-in package.\n"
            "- Verify your orders are correct: unit, billet, reporting date.\n"
            "- Ensure your SRB/OMPF is transferred and current. Missing docs = delayed pay.\n"
            "- Update SGLI beneficiary (SOES online or form SGLV 8286).\n"
            "- Update Page 2 (Record of Emergency Data, NAVMC 10922).\n"
            "- Verify dental readiness — get to Class 1 or 2 before reporting if possible.\n"
            "- Complete PHA if due within 90 days.\n"
            "- Ensure DBIDS (base access) is current or get a visitor pass arranged.\n\n"
            "System enrollments to request/verify:\n"
            "- MOL (Marine Online) — verify access and that your unit shows correctly.\n"
            "- Drill Manager — your new unit needs to add you for IDT pay.\n"
            "- DTS (Defense Travel System) — new unit routing list and approving official.\n"
            "- MROWS — verify you can be placed on orders by the new unit.\n"
            "- MarineNet — training records should follow you, but verify.\n"
            "- Unit communication channels — ask what the unit uses (email distro, group chat, etc.).\n\n"
            "Documents to bring (originals or certified copies):\n"
            "- Military ID (CAC)\n"
            "- Orders to the unit\n"
            "- Last 3 FitReps / PROs (know your reporting history)\n"
            "- PME certificates (all completed courses)\n"
            "- PFT/CFT score sheets (last 2)\n"
            "- Rifle/pistol qualification scores\n"
            "- College transcripts (if applicable, for promotion points)\n"
            "- Driver's license and vehicle registration (for base access)\n"
            "- Civilian employer information (for ESGR / USERRA purposes)\n\n"
            f"{lateral_note}"
            "PHASE 2 — FIRST DRILL DAY: THE FORMAL REPORT\n\n"
            "What to wear:\n"
            "- Service Alphas (Chucks for officers) unless told otherwise by the unit.\n"
            "- Call ahead and confirm — some units do Charlies or Deltas for check-in.\n"
            "- Uniform must be inspection-ready: fresh haircut, ribbons/medals correct, "
            "shoes shined, brass polished, belt buckle aligned.\n"
            "- Bring cammies in a garment bag — you'll likely change after reporting.\n\n"
            "Formal reporting protocol:\n"
            "- Enter the CO's office area. Remove cover indoors (unless under arms).\n"
            "- Approach the CO's desk, halt at attention, render a sharp salute and hold it.\n"
            "- State: '[Rank] [Last Name], reporting for duty, sir/ma'am.'\n"
            "  Example: 'Captain Brown, reporting for duty, sir.'\n"
            "- Hold the salute until it is returned.\n"
            "- The CO will likely say 'at ease' or 'have a seat' — follow their lead.\n"
            "- Be prepared for a brief conversation: where you're from, your background, "
            "what you're looking forward to contributing.\n"
            "- Thank the CO for their time when dismissed.\n"
            "- You may also report to the XO, SgtMaj/1stSgt, and your immediate supervisor.\n\n"
            "Common variations:\n"
            "- Some COs prefer all new joins report together at a specific time.\n"
            "- Some units do the formal report at the next unit formation instead of privately.\n"
            "- If unsure, ask the S-1 or I&I staff how the CO likes to receive new joins.\n"
            "- The 1stSgt/SgtMaj may want to speak with you before or after the CO.\n\n"
            f"{role_note}"
            "PHASE 3 — FIRST DRILL: ADMIN AND ORIENTATION\n\n"
            "Check-in routing sheet (typical stops):\n"
            "- S-1 (Admin): SRB verification, page 2 update, SGLI, unit diary entry, "
            "add to Drill Manager, assign to muster list.\n"
            "- S-3 (Operations): training schedule orientation, assigned to training section/platoon.\n"
            "- S-4 (Logistics): gear issue (782 gear, TA-50 if applicable), CIF account.\n"
            "- S-6 (Comms): email account, access to unit shared drives/systems.\n"
            "- Armory: weapons assignment and serial number recording (if applicable).\n"
            "- Medical/Dental: verify IMR status, schedule any needed appointments.\n"
            "- Supply: uniform items, name tapes, unit patches if applicable.\n"
            "- NBC/CBRN: gas mask fit and serial number.\n"
            "- 1stSgt/SgtMaj: welcome aboard, expectations, unit standards briefing.\n\n"
            "What to learn on day one:\n"
            "- Battle rhythm: when does the unit muster, what time is morning formation, "
            "when is liberty call?\n"
            "- Chain of command: your immediate supervisor, section head, platoon commander/sergeant.\n"
            "- Unit SOPs: where are they, how do you access them between drills?\n"
            "- Drill schedule: get the full fiscal year drill calendar.\n"
            "- AT dates: when is Annual Training, where, what's the plan?\n"
            "- Communication between drills: how does the unit stay in touch?\n"
            "- Key phone numbers: unit duty phone, I&I staff, your section leader.\n\n"
            "PHASE 4 — FIRST 90 DAYS (SETTLING IN)\n\n"
            "- Complete all check-in routing within first 2 drills. Don't let items linger.\n"
            "- Verify your first drill pay posted correctly in MOL/myPay after drill 1.\n"
            "- If pay is wrong, flag it immediately with S-1 — pay errors compound.\n"
            "- Introduce yourself to every section head. Learn the unit's personality.\n"
            "- Ask your reporting senior about FitRep expectations and the reporting timeline.\n"
            "- Find out what PME you need next and start working on it.\n"
            "- Volunteer for a working party or a collateral duty early — it builds credibility.\n"
            "- Get a battle buddy — someone who's been in the unit and knows how things actually work.\n"
            "- Update your session handoff notes in the dashboard so you don't lose continuity.\n\n"
            "COMMON PITFALLS:\n"
            "- Showing up without your SRB/OMPF transferred — delays everything.\n"
            "- Wrong uniform — always confirm beforehand.\n"
            "- Not knowing your own awards/qualifications — you should know your ribbon rack.\n"
            "- Waiting to be told things instead of asking — the unit expects initiative.\n"
            "- Ignoring admin between drills — the 28-day gap is where things die.\n"
            "- Not verifying pay after first drill — catch errors early.\n"
            "- Being passive about PME — slots fill fast and the board doesn't wait.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(_CHECKIN_REFERENCES),
            structured_citations=structured_citations(_CHECKIN_REFERENCES),
            source_trust=source_trust_markers(
                _CHECKIN_REFERENCES,
                notes_prefix="Verify unit-specific check-in procedures with your S-1 and I&I staff.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Are you checking in as an officer or enlisted?",
                "Is this your first unit or a lateral move from another reserve unit?",
                "Do you know what uniform the unit expects for check-in day?",
                "Have your orders and service records already been transferred?",
            ],
        )


def build_checkin_agent() -> CheckinAgent:
    return CheckinAgent()
