from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    FITREP_AWARDS_REFERENCES,
    WRITING_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)

_FITREP_SIGNALS = (
    "fitrep",
    "fitness report",
    "section i",
    "reporting senior",
    "reviewing officer",
    "relative value",
    "performance evaluation",
)
_AWARDS_SIGNALS = (
    "award",
    "citation",
    "summary of action",
    "navcom",
    "navy achievement",
    "achievement medal",
    "commendation medal",
    "meritorious service medal",
    "end of tour",
    "impact award",
    "iaps",
)


def _requested_mode(context: AgentContext) -> str | None:
    options = context.extra.get("agent_options")
    mode = options.get("mode") if isinstance(options, dict) else None
    return mode if isinstance(mode, str) and mode else None


class WritingBriefingCoachAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="writing-briefing-coach",
            name="Writing / Briefing Coach",
            description=(
                "Sharpens staff writing and briefing quality by focusing on audience, decision, structure, evidence, "
                "and brevity. Includes a FitRep & awards mode for Section I comments, RO comments, summaries of "
                "action, and citations."
            ),
            domain="communication",
            intended_users=["SMCR officers", "staff officers", "XO", "command teams", "reporting seniors", "S-1"],
            allowed_sources=[
                "public correspondence guidance",
                "public command and staff PME references",
                "public performance evaluation and awards manuals",
                "local training-only staff products",
            ],
            disallowed_inputs=[
                "classified or sensitive official products in unapproved environments",
                "PII beyond what the draft itself requires (no SSNs, EDIPIs, or medical detail)",
            ],
            system_prompt=(
                "Respond like a command-and-staff writing coach. Help the user produce cleaner briefs and products "
                "without smothering them in academic language.\n\n"
                "Key format references:\n"
                "- Naval letter: standard military correspondence format (MCO 5216.20B, SECNAV M-5216.5).\n"
                "- Point paper: 1-page single-issue summary — issue, background, discussion, recommendation.\n"
                "- White paper: longer analytical product with executive summary, analysis, and recommendations.\n"
                "- Decision brief: problem, options with pros/cons, recommendation, decision requested.\n"
                "- Staff estimate: mission, situation, COA analysis, comparison, recommendation.\n"
                "- AAR: sustains, improves, and corrective actions tied to training objectives.\n"
                "- DD Form 2977: deliberate risk assessment worksheet for training events.\n\n"
                "Common writing failures to catch:\n"
                "- Burying the recommendation below the background.\n"
                "- Missing the audience — writing for peers when the reader is the commander.\n"
                "- Assumptions hiding in the prose instead of being stated explicitly.\n"
                "- Products that describe the process instead of answering the question.\n\n"
                "FITREP & AWARDS MODE (agent_options.mode = 'fitrep_awards', or when the request mentions "
                "FitReps, Section I, awards, citations, or summaries of action). Facts as of Sep 2026 — verify "
                "against MCO 1610.7B and SECNAV M-1650.1 / MCO 1650.19 before submission:\n"
                "- Reporting chain: Marine Reported On (MRO) → Reporting Senior (RS) → Reviewing Officer (RO); "
                "a third officer sighter (3O) is required in the cases the PES Manual specifies. Sgt and above "
                "receive FitReps; Cpl and below receive proficiency/conduct marks.\n"
                "- Sections: A admin, B billet description, C billet accomplishments, D mission accomplishment "
                "(performance, proficiency), E individual character (courage, effectiveness under stress, "
                "initiative), F leadership (leading subordinates, developing subordinates, setting the example, "
                "ensuring well-being of subordinates, communication skills), G intellect and wisdom (PME, "
                "decision-making ability, judgment), H fulfillment of evaluation responsibilities, I directed and "
                "additional comments (RS narrative), J certification, K RO comments and comparative assessment. "
                "That is 14 graded attributes; marks A–G, with H = not observed (excluded from the average).\n"
                "- Relative value (RV): the MRO's report is compared to the RS's own profile (RS average = 80; "
                "RS high = 100). Inflation destroys the RS's profile, so marks must be earned and the Section I "
                "must justify them. The RO's Section K comparative assessment is an 8-block 'Christmas tree' "
                "against all Marines of that grade the RO has evaluated.\n"
                "- Section I discipline: open with a one-sentence summary evaluation and a promotion/retention "
                "recommendation, then 3–5 quantified accomplishments tied to billet impact, then potential. "
                "No adjectives without evidence; no restating Section C; directed comments (adverse, 3O sighted, "
                "not recommended, etc.) exactly as the PES Manual requires.\n"
                "- Occasions and timing: annual, change of RS, transfer, end of service, grade change, and the "
                "reserve-specific occasions for AT/ADT periods; reports are due to HQMC within the window after "
                "the ending date (verify the current day count and minimum observation period). Submit through "
                "APES/MOL.\n"
                "- Adverse reports: the MRO must be given the report and the right to submit a rebuttal statement "
                "before it goes to the RO.\n"
                "- Awards (SECNAV M-1650.1 / MCO 1650.19): package = recommendation form (OPNAV 1650/3 or iAPS "
                "entry), summary of action (SOA), proposed citation. Awarding authority rises with the award "
                "(NAM at the O-5/O-6 command level, NCM at the general-officer level, MSM at the flag/general "
                "level — verify the current delegation table). Match the award to the scope and impact of the "
                "achievement, not to rank or time in billet.\n"
                "- SOA: bulletized, quantified, specific, and time-bound; state the impact on the unit's mission; "
                "compare to what the billet normally requires. The SOA carries the evidence; the citation "
                "carries the impact in the manual's line/character limit.\n"
                "- Citation format: opening ('For professional achievement / superior performance of his or her "
                "duties while serving as [billet], [unit], from [dates]'), body (2–4 specific, impact-stated "
                "achievements), closing ('...reflected great credit upon [himself/herself] and upheld the "
                "highest traditions of the Marine Corps and the United States Naval Service').\n"
                "- Reserve reality: end-of-tour and AT awards must be started before the Marine departs; drill "
                "gaps kill packages. Route through the S-1 awards tracker with suspense dates."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        mode = _requested_mode(context)
        lowered = input_text.lower()
        fitrep_hit = any(signal in lowered for signal in _FITREP_SIGNALS)
        awards_hit = any(signal in lowered for signal in _AWARDS_SIGNALS)
        if mode == "fitrep_awards" or (mode is None and (fitrep_hit or awards_hit)):
            return self._fitrep_awards_response(input_text, fitrep_first=fitrep_hit or not awards_hit)
        return self._coach_response(input_text)

    def _coach_response(self, input_text: str) -> AgentRunResponse:
        answer = (
            "Writing / briefing coach advisory.\n\n"
            "Use this when the product exists but the thinking is getting lost in the prose.\n\n"
            "Pressure these questions:\n"
            "- Who is the audience?\n"
            "- What decision or understanding is required?\n"
            "- What belongs in the main body, and what belongs in backup?\n"
            "- What claim needs evidence or a source note?\n"
            "- What can be cut without losing the point?\n\n"
            "Good staff-product habits:\n"
            "- Lead with the problem, decision, or recommendation.\n"
            "- Use headings that reflect thought, not paperwork.\n"
            "- Keep each paragraph doing one job.\n"
            "- Make assumptions and caveats explicit instead of hiding them in tone.\n"
            "- Build slides and briefs around what the commander must grasp quickly.\n"
            "- If the product is clean but the logic is weak, fix the logic first.\n\n"
            "For FitRep Section I comments, RO comments, award summaries of action, or citations, ask for the "
            "FitRep & awards mode (or set mode=fitrep_awards).\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(WRITING_REFERENCES),
            structured_citations=structured_citations(WRITING_REFERENCES),
            source_trust=source_trust_markers(
                WRITING_REFERENCES,
                notes_prefix="Verify current correspondence and PME references before formal use.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Who is the audience for this product or brief?",
                "What decision or understanding should the audience leave with?",
                "What part belongs in backup instead of the main product?",
            ],
        )

    def _fitrep_awards_response(self, input_text: str, *, fitrep_first: bool) -> AgentRunResponse:
        fitrep_block = (
            "FITREP WRITING (MCO 1610.7B — facts as of Sep 2026, verify before submission):\n"
            "- Chain: MRO → Reporting Senior (RS) → Reviewing Officer (RO), plus a third officer sighter (3O) "
            "where the PES Manual requires one. Sgt and above get FitReps.\n"
            "- The 14 attributes (Sections D–H): performance, proficiency; courage, effectiveness under stress, "
            "initiative; leading subordinates, developing subordinates, setting the example, ensuring well-being "
            "of subordinates, communication skills; PME, decision-making ability, judgment; evaluations. "
            "Marks A–G; H = not observed and is excluded from the average.\n"
            "- Relative value: every mark moves the RS's own profile. RS average = 80, RS high = 100. Mark to "
            "what was observed and let Section I carry the argument.\n"
            "- Section I structure that works:\n"
            "  1. One-sentence summary evaluation (where this Marine stands among peers you have rated).\n"
            "  2. Promotion / retention / school recommendation, stated plainly.\n"
            "  3. Three to five quantified accomplishments tied to billet impact (numbers, scope, outcome).\n"
            "  4. Potential: what billet or responsibility this Marine is ready for next.\n"
            "  Directed comments exactly as the PES Manual prescribes; no restating Section C; no adjectives "
            "without evidence.\n"
            "- RO Section K: comparative assessment against all Marines of that grade the RO has reviewed, plus "
            "comments that address the RS's evaluation, not a second narrative.\n"
            "- Timing: know the occasion (annual, change of RS, transfer, end of service, grade change, "
            "reserve AT/ADT occasions) and the submission window after the ending date; submit through "
            "APES/MOL. Adverse reports go to the MRO for acknowledgement and rebuttal before the RO.\n"
            "- Reserve friction: RS changes between drills and 28-day gaps make late reports the norm; the S-1 "
            "tracker should show every MRO, occasion, ending date, and RS.\n\n"
        )
        awards_block = (
            "AWARD WRITING (SECNAV M-1650.1 / MCO 1650.19 — facts as of Sep 2026, verify before submission):\n"
            "- Package: recommendation (OPNAV 1650/3 or the iAPS entry), summary of action (SOA), proposed "
            "citation. Awarding authority rises with the award (NAM → NCM → MSM); confirm the current delegation "
            "table and route through the S-1 awards tracker with a suspense.\n"
            "- Pick the award by scope and impact of the achievement, not by rank, time in billet, or 'everyone "
            "gets one on departure.' If the SOA cannot show impact beyond the billet's normal expectations, the "
            "package is a letter of appreciation, not a medal.\n"
            "- SOA: bulletized, quantified, specific, time-bound. Each bullet = what the Marine did, the scale "
            "(numbers, dollars, Marines, events), and the result for the unit's mission. Compare to the billet "
            "norm. No character adjectives.\n"
            "- Citation skeleton: 'For professional achievement in the superior performance of [his/her] duties "
            "while serving as [billet], [unit], from [month year] to [month year]. [Two to four sentences: "
            "specific, impact-stated achievements drawn from the SOA.] [Rank] [Name]'s [initiative, perseverance, "
            "and total dedication to duty] reflected great credit upon [him/her] and were in keeping with the "
            "highest traditions of the Marine Corps and the United States Naval Service.' Stay inside the "
            "manual's line/character limit for the award type.\n"
            "- Timeliness: end-of-tour and AT awards start before the Marine leaves; late submissions require "
            "justification and usually die.\n\n"
        )
        ordered = fitrep_block + awards_block if fitrep_first else awards_block + fitrep_block
        answer = (
            "Writing / briefing coach — FitRep & awards mode.\n\n"
            "Use this to build a defensible, specific write-up. It is not the reporting senior's judgment and "
            "does not replace the PES Manual or the Awards Manual.\n\n"
            + ordered
            + "Before you send it, check:\n"
            "- Does every claim have a number, a scope, or an outcome behind it?\n"
            "- Would the RO or awarding authority understand the impact without knowing the Marine?\n"
            "- Is the recommendation (promotion, school, award level) stated in one plain sentence?\n"
            "- Is anything in the draft PII the reader does not need (SSN, EDIPI, medical detail)?\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(FITREP_AWARDS_REFERENCES),
            structured_citations=structured_citations(FITREP_AWARDS_REFERENCES),
            source_trust=source_trust_markers(
                FITREP_AWARDS_REFERENCES,
                notes_prefix=(
                    "Verify the current PES Manual and Awards Manual change before submitting; the S-1 and the "
                    "reporting senior own the final product."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What billet, reporting period, and occasion (or award level) is this for?",
                "What are the three most significant, quantifiable things this Marine did?",
                "What recommendation should the reader leave with: promote, retain, school, or award level?",
            ],
        )


def build_writing_briefing_agent() -> WritingBriefingCoachAgent:
    return WritingBriefingCoachAgent()
