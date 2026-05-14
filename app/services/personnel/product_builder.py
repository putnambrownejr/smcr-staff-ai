from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.agents import Confidence, StructuredCitation
from app.schemas.personnel import (
    PersonnelDraftSection,
    PersonnelProductRequest,
    PersonnelProductResponse,
    PersonnelProductType,
)


class PersonnelProductBuilder:
    def build(self, request: PersonnelProductRequest) -> PersonnelProductResponse:
        return PersonnelProductResponse(
            product_type=request.product_type,
            title=f"{request.product_type.value.replace('_', ' ').title()}: {request.title}",
            summary=_summary(request),
            sections=_sections(request),
            routing_steps=_routing_steps(request),
            required_documents=_required_documents(request),
            review_points=_review_points(request),
            citations=_citations(request.product_type),
            structured_citations=_structured_citations(request.product_type),
            warnings=_warnings(request),
            follow_up_questions=_follow_up_questions(request),
            confidence=Confidence.low,
        )


def _summary(request: PersonnelProductRequest) -> list[str]:
    lines = [
        "Use this as an advisory draft and review plan, not as an official personnel action.",
        "Verify dates, names, reporting chain, and local command requirements before routing.",
    ]
    if request.subject_name:
        lines.append(f"Subject: {request.subject_name}")
    if request.occasion:
        lines.append(f"Occasion / purpose: {request.occasion}")
    if request.suspense_date:
        lines.append(f"Suspense to verify: {request.suspense_date.isoformat()}")
    if request.routing_chain:
        lines.append(f"Expected routing chain: {' -> '.join(request.routing_chain)}")
    return lines


def _sections(request: PersonnelProductRequest) -> list[PersonnelDraftSection]:
    context_prompts = [
        f"Title: {request.title}",
        *([f"Subject: {request.subject_name}"] if request.subject_name else []),
        *([f"Occasion: {request.occasion}"] if request.occasion else []),
        *([f"User role in workflow: {request.role}"] if request.role else []),
    ]
    fact_prompts = [f"User fact to verify: {fact}" for fact in request.facts]
    achievement_prompts = [f"Achievement or evidence to confirm: {item}" for item in request.achievements]
    constraint_prompts = [f"Constraint: {item}" for item in request.constraints]
    if request.product_type == PersonnelProductType.fitrep_planning:
        base = [
            PersonnelDraftSection(
                heading="Admin Data Check",
                prompts=[
                    "Confirm the reporting occasion, dates, billet title, and reviewing chain.",
                    "Verify the support form, billet description, and accomplishment notes are current.",
                ],
            ),
            PersonnelDraftSection(
                heading="Performance Themes",
                prompts=[
                    "List 3-5 performance themes grounded in documented achievements.",
                    "Tie impact to leadership, warfighting, readiness, or staff execution outcomes.",
                ],
            ),
            PersonnelDraftSection(
                heading="Routing And Review",
                prompts=[
                    "Identify what the MRO, RS, and RO each still need to review or confirm.",
                    "Capture suspense dates, coordination notes, and any missing support.",
                ],
            ),
        ]
    elif request.product_type == PersonnelProductType.fitrep_bullets:
        base = [
            PersonnelDraftSection(
                heading="Achievement Capture",
                prompts=[
                    "Collect measurable achievements, outcomes, and leadership examples.",
                    "Separate direct evidence from impressions or unsupported claims.",
                ],
            ),
            PersonnelDraftSection(
                heading="Potential Draft Bullet Themes",
                prompts=[
                    "Phrase concise action-impact-result bullets.",
                    "Include reserve-specific context such as distributed personnel, "
                    "drill-time constraints, and continuity work when relevant.",
                ],
            ),
            PersonnelDraftSection(
                heading="Substantiation Review",
                prompts=[
                    "Check that each bullet can be backed by notes, products, metrics, or witness review.",
                    "Flag anything that needs confirmation before it appears in a formal draft.",
                ],
            ),
        ]
    elif request.product_type == PersonnelProductType.award_package:
        base = [
            PersonnelDraftSection(
                heading="Nomination Scope",
                prompts=[
                    "Confirm the award level, award period, and exact act/service being recognized.",
                    "Check local command package rules and suspense windows.",
                ],
            ),
            PersonnelDraftSection(
                heading="Supporting Content",
                prompts=[
                    "Organize achievements into strong citation themes and supporting bullets.",
                    "Separate factual accomplishments from praise-only language.",
                ],
            ),
            PersonnelDraftSection(
                heading="Endorsements And Routing",
                prompts=[
                    "Map endorsement sequence, signature authority, and enclosure requirements.",
                    "Identify what must be human-reviewed before routing.",
                ],
            ),
        ]
    else:
        base = [
            PersonnelDraftSection(
                heading="Package Purpose",
                prompts=[
                    "State the requested action, owner, suspense, and decision authority.",
                    "Identify whether the package is information, decision, or signature routing.",
                ],
            ),
            PersonnelDraftSection(
                heading="Routing Stack",
                prompts=[
                    "List references, enclosures, and supporting notes in the order reviewers expect.",
                    "Highlight any required concurrence, coordination, or cover note.",
                ],
            ),
            PersonnelDraftSection(
                heading="Final Review",
                prompts=[
                    "Check formatting, names, dates, and enclosure labeling.",
                    "Confirm the final approval chain and release method.",
                ],
            ),
        ]
    return [
        PersonnelDraftSection(
            heading=section.heading,
            prompts=[*context_prompts, *section.prompts, *fact_prompts, *achievement_prompts, *constraint_prompts],
        )
        for section in base
    ]


def _routing_steps(request: PersonnelProductRequest) -> list[str]:
    default_chain = request.routing_chain or _default_chain(request.product_type)
    steps = [f"Confirm routing participant: {step}" for step in default_chain]
    steps.append("Verify suspense date, required signature authority, and final delivery method.")
    steps.append("Pause for human review before submitting any official personnel package.")
    return steps


def _required_documents(request: PersonnelProductRequest) -> list[str]:
    docs = list(request.document_references)
    if request.product_type in {
        PersonnelProductType.fitrep_planning,
        PersonnelProductType.fitrep_bullets,
    }:
        docs.extend(
            [
                "Current PES / FitRep reference",
                "Support form or accomplishment tracker",
                "Billet description and key duties",
            ]
        )
    elif request.product_type == PersonnelProductType.award_package:
        docs.extend(
            [
                "Award recommendation format",
                "Supporting bullets or summary of action",
                "Prior endorsement or routing guidance",
            ]
        )
    else:
        docs.extend(
            [
                "Draft correspondence or routing note",
                "Enclosure list",
                "Approval chain reference",
            ]
        )
    seen: set[str] = set()
    ordered: list[str] = []
    for item in docs:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            ordered.append(item)
    return ordered


def _review_points(request: PersonnelProductRequest) -> list[str]:
    points = [
        "Verify the package stays UNCLASSIFIED and excludes unnecessary PII.",
        "Check dates, names, billet titles, and reporting chain details against official systems.",
        "Keep all draft language supportable by records, notes, or reviewer-confirmed facts.",
    ]
    if request.product_type in {
        PersonnelProductType.fitrep_planning,
        PersonnelProductType.fitrep_bullets,
    }:
        points.extend(
            [
                "Do not treat this prototype as the place for final marks, comparative "
                "assessment, or official submission.",
                "Confirm the latest PES requirements before routing any FitRep-related product.",
            ]
        )
    elif request.product_type == PersonnelProductType.award_package:
        points.extend(
            [
                "Verify award criteria, command conventions, and evidence thresholds.",
                "Ensure the draft citation and endorsement language match the approved level of award.",
            ]
        )
    else:
        points.extend(
            [
                "Verify final correspondence format against current DON and Marine Corps manuals.",
                "Confirm every enclosure is present and labeled the way the receiving chain expects.",
            ]
        )
    return points


def _citations(product_type: PersonnelProductType) -> list[str]:
    if product_type in {
        PersonnelProductType.fitrep_planning,
        PersonnelProductType.fitrep_bullets,
    }:
        return [
            "MCO 1610.7 Performance Evaluation System",
            "MCRAMM or current Reserve admin references as applicable",
        ]
    if product_type == PersonnelProductType.award_package:
        return [
            "SECNAV M-1650.1 Navy and Marine Corps Awards Manual",
            "Current command or service-level award routing guidance",
        ]
    return [
        "SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
        "MCO 5216.20B Marine Corps Supplement to the DON Correspondence Manual",
    ]


def _structured_citations(product_type: PersonnelProductType) -> list[StructuredCitation]:
    if product_type in {
        PersonnelProductType.fitrep_planning,
        PersonnelProductType.fitrep_bullets,
    }:
        return [
            StructuredCitation(
                title="MCO 1610.7 Performance Evaluation System",
                url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2861459/mco-16107a/",
                publisher="Headquarters Marine Corps",
                confidence=Confidence.low,
                notes="Manifest/source-note citation; verify current MCPEL entry and exact revision before use.",
            )
        ]
    if product_type == PersonnelProductType.award_package:
        return [
            StructuredCitation(
                title="SECNAV M-1650.1 Navy and Marine Corps Awards Manual",
                url="https://www.secnav.navy.mil/doni/SECNAV%20Manuals1/1650.1.pdf",
                publisher="Department of the Navy",
                confidence=Confidence.low,
                notes="Manifest/source-note citation; confirm local command package requirements before routing.",
            )
        ]
    return [
        StructuredCitation(
            title="SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
            url="https://www.secnav.navy.mil/doni/SECNAV%20Manuals1/5216.5%20%20CH-1.pdf",
            publisher="Department of the Navy",
            confidence=Confidence.low,
            notes="Manifest/source-note citation; exact section citation requires RAG ingestion.",
        ),
        StructuredCitation(
            title="MCO 5216.20B Marine Corps Supplement to the DON Correspondence Manual",
            url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2795618/mco-521620b-wadmin-ch-4/",
            publisher="Headquarters Marine Corps",
            confidence=Confidence.low,
            notes="Manifest/source-note citation; verify current MCPEL status before use.",
        ),
    ]


def _warnings(request: PersonnelProductRequest) -> list[str]:
    payload = " ".join(
        [
            request.title,
            request.subject_name or "",
            request.occasion or "",
            *request.facts,
            *request.achievements,
            *request.constraints,
        ]
    )
    warnings = [
        *DEFAULT_WARNINGS,
        *detect_sensitive_input(payload),
        "Personnel product support is advisory only and must be reviewed by the proper admin chain.",
    ]
    if request.product_type in {
        PersonnelProductType.fitrep_planning,
        PersonnelProductType.fitrep_bullets,
    }:
        warnings.append(
            "Do not use this prototype for final official FitRep submission or "
            "comparative assessment decisions."
        )
    return sorted(set(warnings))


def _follow_up_questions(request: PersonnelProductRequest) -> list[str]:
    questions = [
        "What suspense date, approver, or routing step still needs confirmation?",
        "Which facts are documented versus still needing verification?",
    ]
    if request.product_type in {
        PersonnelProductType.fitrep_planning,
        PersonnelProductType.fitrep_bullets,
    }:
        questions.extend(
            [
                "What are the strongest documented accomplishments for the reporting period?",
                "Which part of the reporting chain still needs supporting notes or bullet input?",
            ]
        )
    elif request.product_type == PersonnelProductType.award_package:
        questions.extend(
            [
                "What award level is being considered and over what period?",
                "What evidence best supports the recommended citation themes?",
            ]
        )
    else:
        questions.extend(
            [
                "Who is the final decision authority for this package?",
                "What references or enclosures are mandatory before routing?",
            ]
        )
    return questions


def _default_chain(product_type: PersonnelProductType) -> list[str]:
    if product_type in {
        PersonnelProductType.fitrep_planning,
        PersonnelProductType.fitrep_bullets,
    }:
        return ["MRO", "RS", "RO"]
    if product_type == PersonnelProductType.award_package:
        return ["originator", "endorser", "approval authority"]
    return ["action officer", "reviewer", "approver"]
