from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    LEGAL_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class SjaLegalAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="jag-legal-advisor",
            name="SJA / Military Justice Advisor",
            description=(
                "Supports command legal issue-spotting for NJP, military justice, UCMJ, and command-routing "
                "questions while clearly refusing case-specific legal advice or replacement of the SJA, defense "
                "counsel, victims' legal counsel, or trial counsel."
            ),
            domain="legal support",
            intended_users=["command teams", "staff officers", "Chief of Staff / Aide", "commanders", "XOs"],
            allowed_sources=[
                "official Marine Corps SJA references",
                "official Manual for Courts-Martial references",
                "official Department of the Navy legal-administration references",
                "training-only staff scenarios",
            ],
            disallowed_inputs=[
                "attorney-client privileged content",
                "requests for case-specific legal advice",
                "ongoing investigations with protected details",
                "victim-sensitive information beyond minimum issue-spotting need",
                "classified or CUI legal matters in public tooling",
            ],
            system_prompt=(
                "Respond like a practical staff judge advocate issue-spotter supporting command decision-making. "
                "Be strong on NJP, courts-martial process awareness, UCMJ framing, routing, rights warnings, "
                "and record discipline. Do not give legal advice, do not predict case outcomes, and do not "
                "substitute for the SJA, trial counsel, defense counsel, VLC, or other authorized legal channels."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        context_lines = self._active_context_lines(context)
        context_block = ""
        if context_lines:
            context_block = "\n".join(context_lines) + "\n\n"

        answer = (
            "SJA / military justice advisory draft.\n\n"
            "Use this for command issue-spotting and routing only. It is not legal advice, does not create an "
            "attorney-client relationship, and does not replace the SJA, defense counsel, victims' legal counsel, "
            "trial counsel, or formal legal review.\n\n"
            "Terminology note:\n"
            "- For Marine command support, 'SJA' is the better lane name here.\n"
            "- The repo keeps the legacy agent ID `jag-legal-advisor` only for compatibility.\n\n"
            f"{context_block}"
            "First cut questions:\n"
            "- Is this really an NJP, military justice, administrative-separation, ethics, investigation, or "
            "command-authority question?\n"
            "- Who is the decision-maker, what action is being considered, and what deadline is driving it?\n"
            "- Are there accused, victim, witness, Reserve-component, or concurrent-civilian-jurisdiction facts "
            "that change routing immediately?\n\n"
            "NJP / Article 15 issue-spotting:\n"
            "- Confirm authority to impose NJP, jurisdiction over the accused, and whether Reserve status changes "
            "what can be imposed or when.\n"
            "- Confirm the accused is properly advised, understands any right to refuse NJP when applicable, and "
            "knows appeal and record implications.\n"
            "- Keep the record discipline straight: evidence, UPB preparation, endorsements, and any required judge "
            "advocate review.\n"
            "- If the disposition, available punishment, or procedural path feels uncertain, stop pretending this "
            "is routine and get real SJA review.\n\n"
            "Courts-martial / military justice issue-spotting:\n"
            "- Ask whether the matter is beyond NJP or administrative correction and needs formal military justice "
            "routing.\n"
            "- Protect evidence, preserve notes carefully, and do not turn command curiosity into witness coaching "
            "or unlawful influence.\n"
            "- Watch for pretrial confinement, search and seizure, Article 32, victim-rights, discovery, or "
            "concurrent civilian-jurisdiction issues that require immediate legal coordination.\n"
            "- If the fact pattern touches an actual accused, victim, or real contemplated disposition, move the "
            "case details into the proper legal channel instead of fleshing them out here.\n\n"
            "Exercise legal issue spotter:\n"
            "- Identify ROE/RUF, escalation-of-force, detainee role-play, search, claims, mishap, public-release, "
            "and investigation injects before the exercise is briefed as executable.\n"
            "- Keep training fiction visibly separate from real-world authority, reporting, evidence, and command "
            "action requirements.\n"
            "- Coordinate early with PAO/COMMSTRAT on release authority and OPSEC, with safety on mishap/risk lanes, "
            "with provost on security/detainee injects, and with IG when inspection or complaint boundaries appear.\n"
            "- Write the SJA review trigger into the exercise timeline instead of treating legal review as a final "
            "signature hunt.\n\n"
            "Legal review triggers for an exercise plan:\n"
            "- Any role-play involving detention, searches, law enforcement, escalation of force, protected persons, "
            "claims, real-world injury, public release, imagery, media engagement, or investigation language.\n"
            "- Any plan that asks Marines to act under simulated authorities they may confuse with real authority.\n"
            "- Any actual incident, allegation, injury, property damage, victim/witness issue, or disciplinary "
            "fact.\n\n"
            "What the command team should usually produce next:\n"
            "- A short issue statement.\n"
            "- The contemplated action or decision point.\n"
            "- The status of the member: active, Reserve, attached, transferred, or pending separation.\n"
            "- The timing problem: upcoming travel, drill status, EAS/RECC, appeal deadline, or hearing timeline.\n"
            "- The proper legal handoff lane: SJA, defense, VLC, trial services, or other designated office.\n\n"
            "My read:\n"
            "- Legal staff work gets dangerous when commands confuse 'I roughly know the rule' with 'we are ready "
            "to act.'\n"
            "- The value of this lane is to make the right questions and routing obvious early, not to replace the "
            "lawyer."
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(LEGAL_REFERENCES),
            structured_citations=structured_citations(LEGAL_REFERENCES),
            source_trust=source_trust_markers(
                LEGAL_REFERENCES,
                notes_prefix="Verify current military justice, NJP, and SJA routing authorities before acting.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                (
                    "Is this an NJP issue, a courts-martial issue, an investigation issue, "
                    "or an administrative action question?"
                ),
                "What status is the member in right now, especially if Reserve status or pending transfer matters?",
                (
                    "Which real legal channel should receive the next clean issue statement: "
                    "SJA, defense, VLC, or trial services?"
                ),
            ],
        )


def build_jag_agent() -> SjaLegalAdvisorAgent:
    return SjaLegalAdvisorAgent()
