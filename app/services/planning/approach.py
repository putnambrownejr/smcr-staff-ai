from app.schemas.planning import PlanningApproachAssessment


def assess_planning_approach(
    *,
    title: str,
    mission_or_training_goal: str,
    event_type: str,
    timeframe: str | None,
    constraints: list[str],
    higher_guidance: list[str],
    coordinating_sections: list[str],
    support_requirements: list[str],
    partner_types: list[str],
    civil_considerations: list[str],
    subordinate_unit_count: int = 0,
    source_items_present: bool = False,
    formal_event: bool = False,
    raw_guidance_text: str | None = None,
) -> PlanningApproachAssessment:
    searchable = " ".join(
        [
            title,
            mission_or_training_goal,
            event_type,
            timeframe or "",
            raw_guidance_text or "",
            *constraints,
            *higher_guidance,
            *coordinating_sections,
            *support_requirements,
            *partner_types,
            *civil_considerations,
        ]
    ).lower()

    mcpp_score = 0
    r2p2_score = 0
    why: list[str] = []
    indicators: list[str] = []
    staff_implications: list[str] = []

    complexity_terms = {
        "new",
        "complex",
        "ambiguous",
        "cross-functional",
        "cross functional",
        "partner",
        "civil",
        "interagency",
        "formal event",
        "ceremony",
    }
    time_pressure_terms = {
        "same day",
        "tonight",
        "short notice",
        "rapid",
        "within 6 hours",
        "within six hours",
        "compressed",
        "time-constrained",
        "time constrained",
    }
    familiar_terms = {
        "refine",
        "rehearse",
        "update",
        "existing",
        "standard",
        "routine",
        "sop",
        "familiar",
    }

    if any(term in searchable for term in complexity_terms):
        mcpp_score += 2
        indicators.append("The problem includes complexity cues that usually justify deliberate staff framing.")
    if source_items_present:
        mcpp_score += 1
        indicators.append("Public-source context or intelligence inputs are part of the planning problem.")
    if subordinate_unit_count > 1:
        mcpp_score += 2
        indicators.append("Multiple subordinate/supporting elements must be nested into the same concept.")
    if len(coordinating_sections) >= 4 or len(support_requirements) >= 3:
        mcpp_score += 2
        indicators.append("Several staff sections and support dependencies need deliberate synchronization.")
    if formal_event:
        mcpp_score += 1
        indicators.append("Formal-event control measures and standards argue for deliberate sequencing.")
    if len(higher_guidance) >= 3 or len(constraints) >= 3:
        mcpp_score += 1
        indicators.append("The amount of guidance and constraint suggests the staff still needs shared understanding.")

    if any(term in searchable for term in time_pressure_terms):
        r2p2_score += 2
        indicators.append("The problem contains real time-pressure cues that could justify compressed planning.")
    if any(term in searchable for term in familiar_terms):
        r2p2_score += 1
        indicators.append("The problem looks more like refinement of a familiar event than discovery of a new problem.")
    if subordinate_unit_count <= 1 and len(coordinating_sections) <= 3:
        r2p2_score += 1
        indicators.append("The problem is small enough that a compressed rhythm may be supportable.")

    if mcpp_score >= r2p2_score:
        recommended_method = "mcpp"
        decision = (
            "Use deliberate MCPP as the planning default. The problem still needs shared understanding, "
            "clear staff framing, and explicit decision support before compression helps."
        )
        why = [
            "This looks more like a staff understanding problem than a pure time problem.",
            (
                "Reserve staffs usually pay for premature compression with vague tasks, support drift, "
                "and weak AAR value."
            ),
            (
                "R2P2-style compression should only happen after the unit already understands the problem "
                "and the baseline concept."
            ),
        ]
        staff_implications = [
            "Drive mission analysis, assumptions, and command relationships explicitly before product drafting.",
            (
                "Use the staff cycle to expose what the unit does not yet understand instead of rushing "
                "straight to execution."
            ),
            "Only compress later pieces once the commander, XO, and key sections share the same frame.",
        ]
    else:
        recommended_method = "r2p2"
        decision = (
            "Use a compressed R2P2-style refinement rhythm. The problem appears familiar enough that time, "
            "not understanding, is the dominant constraint."
        )
        why = [
            "This looks like refinement of a known event or concept rather than first-time problem discovery.",
            "Compressed planning only works here if SOPs, baseline products, and staff habits already exist.",
            (
                "If the staff cannot answer basic mission-analysis questions quickly, fall back to "
                "deliberate MCPP instead of pretending speed is competence."
            ),
        ]
        staff_implications = [
            (
                "Treat the cycle as refinement, decision confirmation, and branch rehearsal rather than "
                "full design from scratch."
            ),
            "Keep the product set narrow: decisions, changes, support checks, and immediate suspenses.",
            "Use a TDG or short wargame to verify that the compressed concept is still honest about failure points.",
        ]

    return PlanningApproachAssessment(
        recommended_method=recommended_method,
        decision=decision,
        why=why,
        indicators=indicators,
        staff_implications=staff_implications,
    )
