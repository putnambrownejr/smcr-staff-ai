from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.agents import Confidence, StructuredCitation
from app.schemas.staff_products import (
    StaffProductDraftRequest,
    StaffProductDraftResponse,
    StaffProductSection,
    StaffProductType,
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

AAR_SECTIONS = [
    StaffProductSection(
        heading="1. Event Overview",
        prompts=[
            "Training event, date, audience, objectives",
            "Supported mission or commander's intent",
            "Why this event mattered to the unit, not just that it occurred",
        ],
    ),
    StaffProductSection(
        heading="2. Standards and Task Alignment",
        prompts=[
            "MET/METL or task standard assessed",
            "What right looked like",
            "What was actually observed",
            "Where the standard broke under friction",
        ],
    ),
    StaffProductSection(
        heading="3. Sustains",
        prompts=[
            "What should continue",
            "Why it mattered",
            "What to preserve in the next iteration",
            "Identify deliberate good practice, not lucky improvisation",
        ],
    ),
    StaffProductSection(
        heading="4. Improves",
        prompts=[
            "What should change",
            "What friction drove the shortfall",
            "What needs command attention",
            "State the first fix that changes the next event instead of writing a complaint",
        ],
    ),
    StaffProductSection(
        heading="5. Action Items",
        prompts=[
            "Owner",
            "Suspense",
            "Follow-up requirement",
            "What must be verified before next execution",
            "Tie each item to the next rehearsal, drill, or execution date",
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
    def build(self, request: StaffProductDraftRequest) -> StaffProductDraftResponse:
        sections = _sections_for(request.product_type)
        title = f"{request.product_type.value.upper()} draft scaffold: {request.topic}"
        warnings = [
            *DEFAULT_WARNINGS,
            *detect_sensitive_input(" ".join([request.topic, *request.facts, *request.constraints])),
            "Staff products are advisory drafts and must be reviewed by the appropriate human chain.",
        ]
        if request.product_type in {
            StaffProductType.opord,
            StaffProductType.warno,
            StaffProductType.frago,
            StaffProductType.conop,
        }:
            warnings.append("Use fictional/training-only data unless working in an approved environment.")
        if request.product_type in {
            StaffProductType.naval_letter,
            StaffProductType.memorandum,
            StaffProductType.endorsement,
        }:
            warnings.append("Verify final formatting against current correspondence manuals before release.")
        return StaffProductDraftResponse(
            product_type=request.product_type,
            title=title,
            sections=_enrich_sections(sections, request),
            formatting_notes=_formatting_notes_for(request),
            review_checklist=_review_checklist(request) if request.include_review_checklist else [],
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
    if product_type == StaffProductType.aar:
        return AAR_SECTIONS
    return CORRESPONDENCE_SECTIONS


def _enrich_sections(
    sections: list[StaffProductSection],
    request: StaffProductDraftRequest,
) -> list[StaffProductSection]:
    sensitivity_warnings = detect_sensitive_input(" ".join([request.topic, *request.facts, *request.constraints]))
    context_prompts = [
        f"Topic: {request.topic}",
        *([f"Audience: {request.audience}"] if request.audience else []),
        *([f"Echelon: {request.echelon}"] if request.echelon else []),
        *([f"Preferred format: {request.preferred_format}"] if request.preferred_format else []),
    ]
    if sensitivity_warnings:
        fact_prompts = ["Sensitive details were withheld. Use only generic training-safe placeholders."]
        constraint_prompts = ["Constraint: verify all operational specifics in an approved environment."]
    else:
        fact_prompts = [f"User fact to verify: {fact}" for fact in request.facts]
        constraint_prompts = [f"Constraint: {constraint}" for constraint in request.constraints]
    return [
        StaffProductSection(
            heading=section.heading,
            prompts=[*context_prompts, *section.prompts, *fact_prompts, *constraint_prompts],
        )
        for section in sections
    ]


def _review_checklist(request: StaffProductDraftRequest) -> list[str]:
    checklist = [
        "Confirm the product is UNCLASSIFIED and appropriate for this prototype.",
        "Verify every factual claim against official/public sources or user-confirmed local context.",
        "Assign human owner, reviewer, and suspense.",
        "Remove unnecessary PII and sensitive unit-specific details.",
        "Confirm final product with the appropriate chain before release.",
    ]
    if request.product_type in {
        StaffProductType.opord,
        StaffProductType.warno,
        StaffProductType.frago,
        StaffProductType.conop,
    }:
        checklist.append("Confirm the scenario is fictional/training-only or handled in an approved environment.")
    return checklist


def _formatting_notes_for(request: StaffProductDraftRequest) -> list[str]:
    if request.product_type == StaffProductType.naval_letter:
        return [
            "Use From/To/Via/Subj/Ref/Encl in the header and keep the subject line short and literal.",
            "Write numbered paragraphs that can survive routing edits and endorsements.",
            "Keep the opening paragraph action-oriented: what is being requested, directed, or provided for decision.",
            "Reserve enclosures, references, and routing notes for items that will actually exist in the package.",
            "End with a clear action, suspense, and point of contact instead of a vague courtesy close.",
        ]
    if request.product_type == StaffProductType.memorandum:
        return [
            "Use memorandum format when the product is internal and does not need full naval-letter routing.",
            "Keep the subject plain and administrative, then move quickly to the purpose and required action.",
            "Use short numbered paragraphs and avoid burying the suspense or decision in the discussion section.",
        ]
    if request.product_type == StaffProductType.endorsement:
        return [
            "Anchor the endorsement to the forwarded package and state whether it recommends, concurs, or elevates "
            "an issue.",
            "Keep the endorsement short; do not rewrite the base package unless the deficiency is the point.",
            "Identify unresolved risks, missing enclosures, or command concerns plainly so the next reviewer can act.",
        ]
    if request.product_type == StaffProductType.frago:
        return [
            "A FRAGO should only state what changed from the base order, not restate the whole order out of habit.",
            "Task subordinate elements in plain Marine-staff language with task, purpose, and no-later-than "
            "discipline where possible.",
            "Make sure coordinating instructions separate what is fixed across the force from what subordinate units "
            "may refine locally.",
        ]
    if request.product_type == StaffProductType.conop:
        return [
            "A CONOP should explain how the unit intends to execute, not pretend to be a full OPORD.",
            "State supported/supporting relationships clearly so subordinate units can draft their own local concepts.",
            "Tie assessment language to task standards, decision points, and AAR capture rather than generic "
            "enthusiasm.",
        ]
    if request.product_type == StaffProductType.aar:
        return [
            "Write the AAR like a product the XO or S-3 would keep: standards, observations, friction, and "
            "corrective actions.",
            "Separate deliberate good practice from lucky improvisation so the unit knows what to preserve.",
            "Every improve item should point to the next rehearsal, drill, or execution window.",
        ]
    return []


def _citations_for(product_type: StaffProductType) -> list[str]:
    citations = ["MCDP 5 Planning", "MCDP 6 Command and Control"]
    if product_type in {StaffProductType.naval_letter, StaffProductType.memorandum, StaffProductType.endorsement}:
        citations.extend(
            [
                "SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
                "MCO 5216.20B Marine Corps Supplement to the DON Correspondence Manual",
            ]
        )
    return citations


def _structured_citations_for(product_type: StaffProductType) -> list[StructuredCitation]:
    citations = [
        StructuredCitation(
            title="MCDP 5 Planning",
            url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899841/mcdp-5/",
            publisher="Headquarters Marine Corps",
            confidence=Confidence.low,
            notes="Manifest citation; exact section citation requires RAG ingestion.",
        ),
        StructuredCitation(
            title="MCDP 6 Command and Control",
            url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899771/mcdp-6/",
            publisher="Headquarters Marine Corps",
            confidence=Confidence.low,
            notes="Manifest citation; exact section citation requires RAG ingestion.",
        ),
    ]
    if product_type in {StaffProductType.naval_letter, StaffProductType.memorandum, StaffProductType.endorsement}:
        citations.append(
            StructuredCitation(
                title="SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
                url="https://www.secnav.navy.mil/doni/SECNAV%20Manuals1/5216.5%20%20CH-1.pdf",
                publisher="Department of the Navy",
                confidence=Confidence.low,
                notes="Manifest citation; exact section citation requires RAG ingestion.",
            )
        )
    return citations
