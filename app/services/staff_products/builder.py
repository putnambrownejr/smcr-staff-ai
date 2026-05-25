from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.agents import Confidence, StructuredCitation
from app.schemas.product_templates import ProductTemplateRecord
from app.schemas.staff_products import (
    StaffProductDraftRequest,
    StaffProductDraftResponse,
    StaffProductSection,
    StaffProductType,
)
from app.services.agents.source_refs import (
    CORRESPONDENCE_REFERENCES,
    MAP_REFERENCES,
    OPORD_REFERENCES,
    S2_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    TRAINING_REFERENCES,
    SourceRef,
    citation_titles,
    structured_citations,
)

OPORD_SECTIONS = [
    StaffProductSection(
        heading="1. Situation",
        prompts=["Area of interest/context", "Friendly forces", "Attachments/detachments", "Civil considerations"],
    ),
    StaffProductSection(
        heading="2. Mission",
        prompts=["Who, what, when, where, and why in one clear sentence"],
    ),
    StaffProductSection(
        heading="3. Execution",
        prompts=["Commander's intent", "Concept of operations", "Tasks", "Coordinating instructions"],
    ),
    StaffProductSection(
        heading="4. Administration and Logistics",
        prompts=["Supply", "Transportation", "Medical", "DTS/travel/admin support", "Reporting requirements"],
    ),
    StaffProductSection(
        heading="5. Command and Signal",
        prompts=["Command relationships", "PACE concept", "Reports", "Information management"],
    ),
]

WARNO_SECTIONS = [
    StaffProductSection(heading="Situation", prompts=["What changed or is expected to change?"]),
    StaffProductSection(heading="Mission / Task", prompts=["Likely task, purpose, and timeline"]),
    StaffProductSection(heading="Initial Timeline", prompts=["Key planning events and immediate suspenses"]),
    StaffProductSection(heading="Coordinating Instructions", prompts=["Required coordination and information needs"]),
]

FRAGO_SECTIONS = [
    StaffProductSection(
        heading="Changes",
        prompts=[
            "Only what changed from the base order",
            "State the command decision, changed task, or new control measure in plain language",
        ],
    ),
    StaffProductSection(
        heading="Tasks",
        prompts=[
            "Updated tasks by unit/staff section",
            "Use task, purpose, method, and no-later-than language where possible",
        ],
    ),
    StaffProductSection(
        heading="Coordinating Instructions",
        prompts=[
            "Updated timeline, control measures, reporting",
            "Call out what remains fixed across all subordinate units versus what may be refined locally",
        ],
    ),
]

CONOP_SECTIONS = [
    StaffProductSection(
        heading="1. Purpose and End State",
        prompts=["Supported mission or training problem", "Desired end state", "Main effort"],
    ),
    StaffProductSection(
        heading="2. Unit and Sub-Unit Relationships",
        prompts=[
            "Higher / supported / supporting relationships",
            "Subordinate tasks in Marine-staff language",
            "Coordination requirements and command relationships",
        ],
    ),
    StaffProductSection(
        heading="3. Concept of Execution",
        prompts=[
            "Phasing",
            "Main effort and supporting effort",
            "Decision points",
            "Control measures and required reports",
        ],
    ),
    StaffProductSection(
        heading="4. Support and Sustainment",
        prompts=["Logistics concept", "Medical support", "Reporting and accountability", "Comms dependencies"],
    ),
    StaffProductSection(
        heading="5. Assessment and Transition",
        prompts=["Measures of performance", "Measures of effectiveness", "AAR capture", "Follow-on refinement"],
    ),
]

SITREP_SECTIONS = [
    StaffProductSection(heading="Current Status", prompts=["What is true now?"]),
    StaffProductSection(heading="Significant Events", prompts=["What changed since the last report?"]),
    StaffProductSection(heading="Issues / Risks", prompts=["What needs command or staff attention?"]),
    StaffProductSection(heading="Next 24-72 Hours", prompts=["Expected activity, decisions, and support requirements"]),
]

DECISION_BRIEF_SECTIONS = [
    StaffProductSection(
        heading="Slide 1. Commander Problem and Decision Required",
        prompts=[
            "State the problem in one sentence",
            "State the exact decision or approval being requested",
            "End the slide with the ask, not background",
        ],
    ),
    StaffProductSection(
        heading="Slide 2. Why This Matters Now",
        prompts=[
            "What changed or why the issue is on the board now",
            "Timeline pressure, readiness impact, or opportunity cost",
            "Keep it to the few facts that make the decision urgent",
        ],
    ),
    StaffProductSection(
        heading="Slide 3. Situation and Mission Linkage",
        prompts=[
            "Current status",
            "Higher guidance or commander's intent linkage",
            "What this supports in mission, training, or readiness terms",
        ],
    ),
    StaffProductSection(
        heading="Slide 4. Options or COAs",
        prompts=[
            "Present realistic options only",
            "For each option: what it gives, what it costs, what it risks",
            "Do not create fake options just to fill the slide",
        ],
    ),
    StaffProductSection(
        heading="Slide 5. Risks, Friction, and Assumptions",
        prompts=[
            "What breaks this plan first",
            "Critical assumptions that still need confirmation",
            "Support, comm, medical, admin, or timeline friction",
        ],
    ),
    StaffProductSection(
        heading="Slide 6. Recommendation and Immediate Actions",
        prompts=[
            "Recommended option and why",
            "Immediate actions if approved",
            "Named owners and next suspense point",
        ],
    ),
]

COMMAND_UPDATE_BRIEF_SECTIONS = [
    StaffProductSection(
        heading="Slide 1. Executive Snapshot",
        prompts=[
            "What the commander needs to know in under thirty seconds",
            "Overall posture: on track, slipping, or blocked",
            "Lead with meaning, not chronology",
        ],
    ),
    StaffProductSection(
        heading="Slide 2. Current Status by Main Effort",
        prompts=[
            "What is complete",
            "What is in progress",
            "What remains open",
        ],
    ),
    StaffProductSection(
        heading="Slide 3. What Changed Since the Last Brief",
        prompts=[
            "New facts only",
            "Changes to timeline, support, risk, or command guidance",
            "Do not re-brief stable information out of habit",
        ],
    ),
    StaffProductSection(
        heading="Slide 4. Risks and Friction",
        prompts=[
            "Top blockers",
            "What is trending worse",
            "What requires commander or XO attention",
        ],
    ),
    StaffProductSection(
        heading="Slide 5. Decisions, Support Requirements, and Suspenses",
        prompts=[
            "Decision required now, if any",
            "Support shortfalls or asks",
            "Named suspenses and next touchpoint",
        ],
    ),
]

AAR_SECTIONS = [
    StaffProductSection(
        heading="1. Event and Command Frame",
        prompts=[
            "Training event, date, audience, objectives",
            "Supported mission or commander's intent",
            "Why this event mattered to the unit, not just that it occurred",
            "State the event in a way the XO or S-3 can revisit later without re-learning the context",
        ],
    ),
    StaffProductSection(
        heading="2. Standards and Task Alignment",
        prompts=[
            "MET/METL or task standard assessed",
            "What right looked like",
            "What was actually observed",
            "Where the standard broke under friction",
            "Call out whether the event measured competence, exposed a gap, or only generated activity",
        ],
    ),
    StaffProductSection(
        heading="3. Sustains and What Held",
        prompts=[
            "What should continue",
            "Why it mattered",
            "What to preserve in the next iteration",
            "Identify deliberate good practice, not lucky improvisation",
            "Name which sustain should be protected even if the event gets compressed next drill",
        ],
    ),
    StaffProductSection(
        heading="4. Improves and Where It Broke",
        prompts=[
            "What should change",
            "What friction drove the shortfall",
            "What needs command attention",
            "State the first fix that changes the next event instead of writing a complaint",
            "Identify whether the failure was design, rehearsal, support, supervision, or execution",
        ],
    ),
    StaffProductSection(
        heading="5. Corrective Actions for the Next Event",
        prompts=[
            "Owner",
            "Suspense",
            "Follow-up requirement",
            "What must be verified before next execution",
            "Tie each item to the next rehearsal, drill, or execution date",
            "Make each corrective action specific enough that someone can actually close it",
        ],
    ),
]

IPB_SECTIONS = [
    StaffProductSection(
        heading="1. Define The Operational Environment",
        prompts=[
            "Area of operations, area of interest, and time horizon",
            "Supported mission or training problem",
            "Relevant physical, informational, and civil boundaries",
            "Known facts, assumptions, source caveats, and information gaps",
        ],
    ),
    StaffProductSection(
        heading="2. Describe Environmental Effects",
        prompts=[
            "Terrain, weather, infrastructure, and civil considerations that affect operations",
            "Observation, fields of fire, cover, concealment, obstacles, key terrain, and avenues of approach",
            "Effects on mobility, sustainment, communications, casualty response, and force protection",
            "What the environment enables, restricts, or makes uncertain for friendly and opposing actors",
        ],
    ),
    StaffProductSection(
        heading="3. Evaluate The Threat Or Relevant Actor",
        prompts=[
            "Composition, disposition, capabilities, limitations, and likely intent",
            "Doctrine, TTP, or behavior patterns only when sourced or explicitly assumed for training",
            "Critical vulnerabilities, dependencies, and decision requirements",
            "Confidence level and what collection or staff input would change the assessment",
        ],
    ),
    StaffProductSection(
        heading="4. Determine Threat COAs And Indicators",
        prompts=[
            "Most likely and most dangerous COA or actor behavior",
            "Named indicators and warnings that would confirm or disconfirm each COA",
            "Priority intelligence requirements, information requirements, and collection gaps",
            "Decision points, triggers, and branches the commander or S-3 may need to plan against",
        ],
    ),
    StaffProductSection(
        heading="5. Staff Use And Recommended Outputs",
        prompts=[
            "Commander implications, risk to mission, and recommended focus areas",
            (
                "Specific products or graphics needed: overlays, event template, COA sketch, collection matrix, "
                "or annex input"
            ),
            "Cross-staff friction for S-3, S-4, S-6, medical, force protection, and CA/G-9",
            "What must be verified before this IPB can support an order, brief, or exercise design",
        ],
    ),
]

CORRESPONDENCE_SECTIONS = [
    StaffProductSection(
        heading="Header / Routing",
        prompts=[
            "From, to, via, subject, references, enclosures",
            "Use the exact command/activity names and routing chain that should appear on the final product",
        ],
    ),
    StaffProductSection(
        heading="Purpose",
        prompts=[
            "Short opening paragraph that states the action or information",
            "Lead with the ask, decision, or notification instead of a long throat-clearing paragraph",
        ],
    ),
    StaffProductSection(
        heading="Discussion",
        prompts=[
            "Plain-language supporting paragraphs",
            "Use numbered paragraphs and subparagraphs that can survive routing edits without losing sequence",
        ],
    ),
    StaffProductSection(
        heading="Action / Closing",
        prompts=[
            "Required action, deadline, approval, or point of contact",
            "Name who owes what by when and what package component or coordination still must be attached",
        ],
    ),
]


class StaffProductBuilder:
    def build(
        self,
        request: StaffProductDraftRequest,
        templates: list[ProductTemplateRecord] | None = None,
    ) -> StaffProductDraftResponse:
        applied_templates = templates or []
        sections = _sections_for(request.product_type)
        title = f"{request.product_type.value.upper()} draft scaffold: {request.topic}"
        warnings = [
            *DEFAULT_WARNINGS,
            *detect_sensitive_input(" ".join([request.topic, *request.facts, *request.constraints])),
            "Staff products are advisory drafts and must be reviewed by the appropriate human chain.",
        ]
        if applied_templates:
            warnings.append(
                "Local templates are reusable examples only. Scrub stale names, "
                "routing, dates, and unit-specific details."
            )
        if request.product_type in {
            StaffProductType.opord,
            StaffProductType.warno,
            StaffProductType.frago,
            StaffProductType.conop,
            StaffProductType.ipb,
        }:
            warnings.append("Use fictional/training-only data unless working in an approved environment.")
        if request.product_type == StaffProductType.ipb:
            warnings.append(
                "Treat IPB as an S-2/G-2 decision-support product; use public or training-safe sources unless "
                "working in an approved environment."
            )
        if request.product_type in {
            StaffProductType.naval_letter,
            StaffProductType.memorandum,
            StaffProductType.endorsement,
        }:
            warnings.append("Verify final formatting against current correspondence manuals before release.")
        return StaffProductDraftResponse(
            product_type=request.product_type,
            title=title,
            sections=_enrich_sections(sections, request, applied_templates),
            applied_templates=[template.template_name for template in applied_templates],
            formatting_notes=_formatting_notes_for(request, applied_templates),
            review_checklist=_review_checklist(request, applied_templates) if request.include_review_checklist else [],
            citations=_citations_for(request.product_type),
            structured_citations=_structured_citations_for(request.product_type),
            warnings=sorted(set(warnings)),
            confidence=Confidence.low,
        )


def _sections_for(product_type: StaffProductType) -> list[StaffProductSection]:
    if product_type == StaffProductType.opord:
        return OPORD_SECTIONS
    if product_type == StaffProductType.warno:
        return WARNO_SECTIONS
    if product_type == StaffProductType.frago:
        return FRAGO_SECTIONS
    if product_type == StaffProductType.conop:
        return CONOP_SECTIONS
    if product_type == StaffProductType.sitrep:
        return SITREP_SECTIONS
    if product_type == StaffProductType.decision_brief:
        return DECISION_BRIEF_SECTIONS
    if product_type == StaffProductType.command_update_brief:
        return COMMAND_UPDATE_BRIEF_SECTIONS
    if product_type == StaffProductType.aar:
        return AAR_SECTIONS
    if product_type == StaffProductType.ipb:
        return IPB_SECTIONS
    return CORRESPONDENCE_SECTIONS


def _enrich_sections(
    sections: list[StaffProductSection],
    request: StaffProductDraftRequest,
    templates: list[ProductTemplateRecord],
) -> list[StaffProductSection]:
    sensitivity_warnings = detect_sensitive_input(" ".join([request.topic, *request.facts, *request.constraints]))
    context_prompts = [
        f"Topic: {request.topic}",
        *([f"Audience: {request.audience}"] if request.audience else []),
        *([f"Echelon: {request.echelon}"] if request.echelon else []),
        *([f"Preferred format: {request.preferred_format}"] if request.preferred_format else []),
    ]
    template_prompts: list[str] = []
    for template in templates:
        template_prompts.append(
            f"Local template reference: {template.template_name} "
            f"({template.template_type.value}). Use as structure only."
        )
        if template.audience_hint:
            template_prompts.append(f"Template audience hint: {template.audience_hint}")
        if template.preferred_format:
            template_prompts.append(f"Template preferred format: {template.preferred_format}")
        template_prompts.extend(
            f"Template heading to consider: {heading}" for heading in template.reusable_headings[:6]
        )
        template_prompts.extend(f"Template reuse note: {note}" for note in template.reusable_guidance[:4])
    if sensitivity_warnings:
        fact_prompts = ["Sensitive details were withheld. Use only generic training-safe placeholders."]
        constraint_prompts = ["Constraint: verify all operational specifics in an approved environment."]
    else:
        fact_prompts = [f"User fact to verify: {fact}" for fact in request.facts]
        constraint_prompts = [f"Constraint: {constraint}" for constraint in request.constraints]
    return [
        StaffProductSection(
            heading=section.heading,
            prompts=[*context_prompts, *template_prompts, *section.prompts, *fact_prompts, *constraint_prompts],
        )
        for section in sections
    ]


def _review_checklist(request: StaffProductDraftRequest, templates: list[ProductTemplateRecord]) -> list[str]:
    checklist = [
        "Confirm the product is UNCLASSIFIED and appropriate for this prototype.",
        "Verify every factual claim against official/public sources or user-confirmed local context.",
        "Assign human owner, reviewer, and suspense.",
        "Remove unnecessary PII and sensitive unit-specific details.",
        "Confirm final product with the appropriate chain before release.",
    ]
    if templates:
        checklist.append(
            "Check every borrowed template element for stale names, dates, "
            "routing, attachments, and unit-specific assumptions."
        )
    if request.product_type in {
        StaffProductType.opord,
        StaffProductType.warno,
        StaffProductType.frago,
        StaffProductType.conop,
        StaffProductType.ipb,
    }:
        checklist.append("Confirm the scenario is fictional/training-only or handled in an approved environment.")
    if request.product_type == StaffProductType.ipb:
        checklist.extend(
            [
                "Confirm S-2/G-2 review before using the IPB to drive commander decisions or exercise injects.",
                "Label assumptions, confidence, and source gaps instead of presenting estimates as settled facts.",
                "Separate public-source environmental context from threat or actor assessments.",
            ]
        )
    if request.product_type in {StaffProductType.decision_brief, StaffProductType.command_update_brief}:
        checklist.extend(
            [
                "Cut any slide that does not change understanding, decision quality, or execution.",
                "Limit each slide to one main point and no more than a few support bullets.",
                "Move narrative paragraphs, source detail, and backup data to speaker notes or an annex.",
                "Make the decision, ask, or suspense explicit before the brief leaves the staff level.",
            ]
        )
    if request.product_type == StaffProductType.aar:
        checklist.extend(
            [
                (
                    "Tie every improve item to a named owner, suspense, and the next drill, rehearsal, "
                    "or execution window."
                ),
                (
                    "Separate standard failure from support, rehearsal, supervision, or design failure "
                    "before finalizing the AAR."
                ),
                (
                    "Strip out complaint language and preserve only observations, friction, decisions, "
                    "and corrective action."
                ),
            ]
        )
    return checklist


def _formatting_notes_for(
    request: StaffProductDraftRequest,
    templates: list[ProductTemplateRecord],
) -> list[str]:
    shared_notes = (
        [
            (
                "A local example template was applied. Preserve useful structure and tone, "
                "but rewrite stale specifics before release."
            )
        ]
        if templates
        else []
    )
    if request.product_type == StaffProductType.naval_letter:
        return [
            *shared_notes,
            "Use From/To/Via/Subj/Ref/Encl in the header and keep the subject line short and literal.",
            "Write numbered paragraphs that can survive routing edits and endorsements.",
            "Keep the opening paragraph action-oriented: what is being requested, directed, or provided for decision.",
            "Reserve enclosures, references, and routing notes for items that will actually exist in the package.",
            "End with a clear action, suspense, and point of contact instead of a vague courtesy close.",
        ]
    if request.product_type == StaffProductType.memorandum:
        return [
            *shared_notes,
            "Use memorandum format when the product is internal and does not need full naval-letter routing.",
            "Keep the subject plain and administrative, then move quickly to the purpose and required action.",
            "Use short numbered paragraphs and avoid burying the suspense or decision in the discussion section.",
        ]
    if request.product_type == StaffProductType.endorsement:
        return [
            *shared_notes,
            "Anchor the endorsement to the forwarded package and state whether it recommends, concurs, or elevates "
            "an issue.",
            "Keep the endorsement short; do not rewrite the base package unless the deficiency is the point.",
            "Identify unresolved risks, missing enclosures, or command concerns plainly so the next reviewer can act.",
        ]
    if request.product_type == StaffProductType.frago:
        return [
            *shared_notes,
            "A FRAGO should only state what changed from the base order, not restate the whole order out of habit.",
            "Task subordinate elements in plain Marine-staff language with task, purpose, and no-later-than "
            "discipline where possible.",
            "Make sure coordinating instructions separate what is fixed across the force from what subordinate units "
            "may refine locally.",
        ]
    if request.product_type == StaffProductType.conop:
        return [
            *shared_notes,
            "A CONOP should explain how the unit intends to execute, not pretend to be a full OPORD.",
            "State supported/supporting relationships clearly so subordinate units can draft their own local concepts.",
            "Tie assessment language to task standards, decision points, and AAR capture rather than generic "
            "enthusiasm.",
        ]
    if request.product_type == StaffProductType.decision_brief:
        return [
            *shared_notes,
            "Treat each section like a slide, not a memo paragraph.",
            "Put one decision problem on the screen at a time; background belongs only where it changes the decision.",
            "Use short bullets, not prose blocks. If it cannot be briefed aloud in a few seconds, it is too dense.",
            "End with a recommendation, immediate actions, and the exact decision or approval required.",
            "Keep backup data off the main slides and move it to annex slides or speaker notes.",
        ]
    if request.product_type == StaffProductType.command_update_brief:
        return [
            *shared_notes,
            "This brief should update command understanding, not restate the whole plan from scratch.",
            "Lead with posture, changes, and blockers before detail.",
            "Use one idea per slide and cut decorative language, slogans, and filler transitions.",
            (
                "If a slide has no decision, support ask, or readiness consequence, "
                "it probably does not belong in the brief."
            ),
        ]
    if request.product_type == StaffProductType.aar:
        return [
            *shared_notes,
            "Write the AAR like a product the XO or S-3 would keep: standards, observations, friction, and "
            "corrective actions worth revisiting later.",
            "Separate deliberate good practice from lucky improvisation so the unit knows what to preserve.",
            "Every improve item should point to the next rehearsal, drill, or execution window.",
            "Lead with what mattered, what held, where the standard broke, and what changes before the next event.",
            "Avoid diary language. Capture judgment, friction, and decisions that shape the next cycle.",
        ]
    if request.product_type == StaffProductType.ipb:
        return [
            *shared_notes,
            "IPB should support decisions and planning, not become a generic terrain, weather, or country brief.",
            (
                "Keep each estimate tied to commander decisions, S-3 planning, collection needs, "
                "or exercise inject design."
            ),
            (
                "Use most-likely and most-dangerous COAs only when they are sourced, explicitly fictional, "
                "or clearly assumed."
            ),
            (
                "Label assumptions, confidence, and information gaps so the staff knows what still needs "
                "collection or review."
            ),
        ]
    return shared_notes


def _citations_for(product_type: StaffProductType) -> list[str]:
    return citation_titles(_source_refs_for(product_type))


def _structured_citations_for(product_type: StaffProductType) -> list[StructuredCitation]:
    citations = structured_citations(_source_refs_for(product_type))
    for citation in citations:
        citation.confidence = Confidence.low
        citation.notes = f"{citation.notes} Exact section citation requires RAG ingestion."
    return citations


def _source_refs_for(product_type: StaffProductType) -> tuple[SourceRef, ...]:
    if product_type in {StaffProductType.naval_letter, StaffProductType.memorandum, StaffProductType.endorsement}:
        return (*CORRESPONDENCE_REFERENCES, *OPORD_REFERENCES)
    if product_type == StaffProductType.aar:
        return (*TRAINING_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.sitrep:
        return STAFF_PRODUCT_REFERENCES
    if product_type == StaffProductType.ipb:
        return (*S2_REFERENCES, *MAP_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type in {
        StaffProductType.opord,
        StaffProductType.warno,
        StaffProductType.frago,
        StaffProductType.conop,
        StaffProductType.decision_brief,
        StaffProductType.command_update_brief,
    }:
        return STAFF_PRODUCT_REFERENCES
    return OPORD_REFERENCES
