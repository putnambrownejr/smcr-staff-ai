from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    UNIFORM_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class UniformAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="uniform-advisor",
            name="Uniform Advisor Agent",
            description="Provides advisory uniform-prep and standards guidance grounded in public regulations.",
            domain="uniforms",
            intended_users=["SMCR Marines", "staff officers", "SEL", "command teams"],
            allowed_sources=["public uniform regulations", "public uniform board references", "public MARADMINs"],
            disallowed_inputs=[
                "disciplinary PII",
                "private personnel records",
                "official command authority impersonation",
            ],
            system_prompt=(
                "Provide Marine Corps uniform standards guidance grounded in MCO 1020.34H and the "
                "Marine Corps Uniform Board. Focus on preparation, serviceability, and ambiguity "
                "reduction. Require chain-of-command review for edge cases.\n\n"
                "Key regulation knowledge:\n"
                "- MCO 1020.34H (with changes) is the primary uniform regulation. Cite the specific "
                "paragraph when answering a wear question; do not quote chapter numbers from memory.\n"
                "- Seasonal uniform periods (summer: sleeves rolled, short-sleeve service shirt; winter: "
                "sleeves down, long-sleeve shirt) are set by the local commanding general, not fixed "
                "service-wide dates. Reserve units follow the I&I / gaining command's published dates. "
                "'Summer whites' is a Navy term; do not use it for Marines.\n"
                "- Service uniform hierarchy: Service 'A' (coat + ribbons), Service 'B' (long-sleeve "
                "khaki shirt + tie), Service 'C' (short-sleeve khaki shirt, no tie). Service 'A' is the "
                "standard for formal occasions; Service 'C' is the common daily garrison uniform.\n"
                "- Dress uniforms: Blue Dress 'A' (medals), Blue Dress 'B' (ribbons), Blue Dress 'C' "
                "(long-sleeve khaki shirt, tie, ribbons), Blue Dress 'D' (short-sleeve khaki shirt, "
                "ribbons). Evening Dress for formal events.\n"
                "- Ribbon precedence: personal decorations first (Medal of Honor, Navy Cross, DSM, Silver "
                "Star, ... NAM, Combat Action Ribbon), then unit awards (PUC, JMUA, NUC, MUC), then "
                "campaign/service awards, then foreign awards. PUC is a unit award, not first overall. "
                "Verify the current precedence chart on the Uniform Board site.\n"
                "- Common inspection discrepancies: loose threads, missing/wrong rank insignia, "
                "improperly spaced ribbons, non-regulation haircuts, unserviceable covers, missing "
                "belt buckle alignment, wrong color undershirt, unauthorized accessories.\n"
                "- CAMMIES (MCCUU/MARPAT): woodland vs desert based on CG guidance. No starching. "
                "Sleeves rolled during the summer season (reinstated 2014), down during winter; never "
                "cuffed. Boot bands required. Name tapes/rank/EGA placement per MCO 1020.34H.\n"
                "- Undershirt: green (olive) crew-neck with MCCUU; verify the authorized undershirt for "
                "service/dress uniforms in MCO 1020.34H before answering (tan undershirts are Army).\n"
                "- PT uniform: green-on-green (shorts/shirt with unit affiliation), or MCCS issued gear. "
                "Seasonal cold-weather PT gear per local command.\n"
                "- Grooming: hair above collar (male), secured above collar (female). Bulk standards. "
                "Mustache within corners of mouth, no other facial hair.\n"
                "- Reserve-specific: uniform allowance timing, sea bag inspection at AT, wear of "
                "civilian attire during travel to/from drill, local I&I uniform of the day guidance."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Uniform advisory draft.\n\n"
            "Use this to shape preparation and standards checks, not to override current command guidance.\n\n"
            "Primary uniform lenses:\n"
            "- What event, formation, or ceremony is driving the uniform question?\n"
            "- What part of the standard is clear, and what part still needs command or SEL verification?\n"
            "- What can be fixed before drill instead of discovered at formation?\n\n"
            "Quick reference — common uniform occasions:\n"
            "| Occasion | Typical uniform | Notes |\n"
            "| Formation / muster | Service C (garrison) or MCCUU | Per unit SOP |\n"
            "| Promotion ceremony | Service A or Blue Dress B | CO discretion |\n"
            "| Birthday Ball | Blue Dress A (medals) or Evening Dress | MARADMIN specifies |\n"
            "| AT field ops | MCCUU (woodland/desert per CG) | Full combat load |\n"
            "| PFT/CFT | Green-on-green PT gear | Seasonal cold-wx allowed |\n"
            "| Travel to/from drill | Civilian attire (unless directed) | Reserve SOP |\n\n"
            "Seasonal uniform period:\n"
            "- Summer season: sleeves rolled on MCCUU, short-sleeve service shirt (Service C).\n"
            "- Winter season: sleeves down, long-sleeve service shirt (Service B).\n"
            "- Changeover dates are set by the local commanding general — confirm the I&I / base "
            "guidance before drill weekend; do not assume another installation's dates.\n\n"
            "Pre-drill uniform checklist:\n"
            "- Confirm uniform of the day (check unit drill notice / I&I guidance).\n"
            "- Inspect serviceability: loose threads, stains, missing buttons, tarnished brass.\n"
            "- Verify rank, ribbon, and insignia placement per MCO 1020.34H.\n"
            "- Check grooming standard compliance (hair, facial hair, fingernails).\n"
            "- Stage required accessories: belt/buckle aligned, covers, gloves (seasonal).\n"
            "- Verify name tapes and USMC tape condition on utilities.\n"
            "- Separate known-good regulation questions from ambiguous local-execution questions.\n"
            "- Route edge cases to the chain of command or SEL before drill.\n\n"
            "Common inspection failures:\n"
            "- Improperly spaced ribbons or wrong precedence order\n"
            "- Non-regulation haircut discovered at formation\n"
            "- Unserviceable cover (bent brim, dirty, faded)\n"
            "- Wrong undershirt (green crew-neck goes with MCCUU; verify the service-uniform undershirt in MCO 1020.34H)\n"
            "- Missing/wrong EGA placement on covers or collar\n"
            "- Belt buckle misaligned with shirt seam\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(UNIFORM_REFERENCES),
            structured_citations=structured_citations(UNIFORM_REFERENCES),
            source_trust=source_trust_markers(
                UNIFORM_REFERENCES,
                notes_prefix=(
                    "Verify the current regulation version and local command guidance "
                    "before final wear decisions."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What event or evolution is driving the uniform question?",
                "Is there local command guidance or a seasonal variation that needs to be checked?",
                "What ambiguity should be routed now so it does not become a formation problem later?",
            ],
        )


def build_uniform_agent() -> UniformAdvisorAgent:
    return UniformAdvisorAgent()
