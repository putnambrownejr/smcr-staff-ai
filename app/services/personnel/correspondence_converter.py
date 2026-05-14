from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.agents import Confidence, StructuredCitation
from app.schemas.personnel import (
    CorrespondenceConversionRequest,
    CorrespondenceConversionResponse,
    CorrespondenceFormatType,
    CorrespondenceSection,
)


class CorrespondenceConverter:
    def build(self, request: CorrespondenceConversionRequest) -> CorrespondenceConversionResponse:
        return CorrespondenceConversionResponse(
            format_type=request.format_type,
            title=f"{request.format_type.value.replace('_', ' ').title()}: {request.title}",
            summary=_summary(request),
            required_headers=_required_headers(request.format_type),
            sections=_sections(request),
            routing_notes=_routing_notes(request),
            review_points=_review_points(request),
            citations=[
                "SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
                "MCO 5216.20B Marine Corps Supplement to the DON Correspondence Manual",
            ],
            structured_citations=_structured_citations(),
            warnings=_warnings(request),
            follow_up_questions=_follow_up_questions(request),
            confidence=Confidence.low,
        )


def _summary(request: CorrespondenceConversionRequest) -> list[str]:
    lines = [
        "This is an advisory conversion scaffold, not an official released document.",
        f"Purpose: {request.purpose}",
        f"Format target: {request.format_type.value.replace('_', ' ')}",
    ]
    if request.audience:
        lines.append(f"Audience / receiving office: {request.audience}")
    if request.references:
        lines.append(f"References to verify: {', '.join(request.references)}")
    if request.enclosures:
        lines.append(f"Potential enclosures: {', '.join(request.enclosures)}")
    return lines


def _required_headers(format_type: CorrespondenceFormatType) -> list[str]:
    if format_type == CorrespondenceFormatType.professional_email:
        return ["From", "To", "Subject", "Action requested / suspense"]
    if format_type == CorrespondenceFormatType.point_paper:
        return ["Issue", "Background", "Discussion", "Recommendation"]
    if format_type == CorrespondenceFormatType.routing_package:
        return ["Action", "Purpose", "Decision required", "Routing chain", "Enclosures"]
    if format_type == CorrespondenceFormatType.endorsement:
        return ["ENDORSEMENT", "Via", "From", "To", "Subj", "Reference(s)", "Enclosure(s)"]
    return ["From", "To", "Subj", "Ref", "Encl", "Body paragraphs"]


def _sections(request: CorrespondenceConversionRequest) -> list[CorrespondenceSection]:
    context_lines = [
        f"Raw source intent: {request.source_text}",
        f"Purpose to preserve: {request.purpose}",
        *[f"Constraint to respect: {item}" for item in request.constraints],
    ]
    if request.format_type == CorrespondenceFormatType.professional_email:
        sections = [
            CorrespondenceSection(
                heading="Subject Line",
                lines=["State the requested action and suspense in one clear line."],
            ),
            CorrespondenceSection(
                heading="Opening",
                lines=["State who you are, why you are writing, and what decision or support is requested."],
            ),
            CorrespondenceSection(
                heading="Supporting Details",
                lines=[
                    "Convert the rough input into short, direct supporting bullets or short paragraphs.",
                    "Preserve dates, suspense items, and required attachments without adding invented facts.",
                ],
            ),
            CorrespondenceSection(
                heading="Closeout",
                lines=["State the requested response, point of contact, and any immediate follow-up required."],
            ),
        ]
    elif request.format_type == CorrespondenceFormatType.point_paper:
            sections = [
                CorrespondenceSection(heading="Issue", lines=["Express the issue in one sentence."]),
            CorrespondenceSection(
                heading="Background",
                lines=[
                    "Condense the source text into only the context needed for the "
                    "decision-maker."
                ],
            ),
            CorrespondenceSection(
                heading="Discussion",
                lines=["Lay out key facts, tradeoffs, and implications in concise bullets."],
            ),
            CorrespondenceSection(heading="Recommendation", lines=["State the decision or action requested."]),
        ]
    else:
        sections = [
            CorrespondenceSection(
                heading="Header Construction",
                lines=[
                    (
                        "Build the title, office lines, subject, references, and "
                        "enclosures in the current DON/USMC format."
                    ),
                    (
                        "Leave placeholders where official office symbols, dates, or "
                        "routing identifiers still need human confirmation."
                    ),
                ],
            ),
            CorrespondenceSection(
                heading="Body Paragraphs",
                lines=[
                    "Convert the raw source text into short, supportable paragraphs with one purpose per paragraph.",
                    "Separate request, justification, and coordination details cleanly.",
                ],
            ),
            CorrespondenceSection(
                heading="Coordination And Routing",
                lines=[
                    "Identify who must review, concur, or sign before release.",
                    "Call out references, enclosures, and suspense items that still need confirmation.",
                ],
            ),
        ]
    return [
        CorrespondenceSection(
            heading=section.heading,
            lines=[*context_lines, *section.lines],
        )
        for section in sections
    ]


def _routing_notes(request: CorrespondenceConversionRequest) -> list[str]:
    notes = [
        "Verify final office symbols, dates, and signature authority before release.",
        "Pause for human review before using the converted draft in any official workflow.",
    ]
    if request.format_type in {
        CorrespondenceFormatType.naval_letter,
        CorrespondenceFormatType.memorandum,
        CorrespondenceFormatType.endorsement,
        CorrespondenceFormatType.routing_package,
    }:
        notes.append("Check whether the package needs concurrence, endorsement, or only information routing.")
    if request.enclosures:
        notes.append("Ensure each enclosure is present, correctly labeled, and referenced in the body if needed.")
    return notes


def _review_points(request: CorrespondenceConversionRequest) -> list[str]:
    return [
        "Do not invent official references, dates, office symbols, or approval language.",
        "Confirm the exact correspondence type expected by the receiving command or staff section.",
        "Keep the draft UNCLASSIFIED and exclude unnecessary PII or sensitive operational detail.",
        *[f"Human review check: {item}" for item in request.constraints],
    ]


def _structured_citations() -> list[StructuredCitation]:
    return [
        StructuredCitation(
            title="SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
            url="https://www.secnav.navy.mil/doni/SECNAV%20Manuals1/5216.5%20%20CH-1.pdf",
            publisher="Department of the Navy",
            confidence=Confidence.low,
            notes="Manifest/source-note citation; verify exact formatting section before final use.",
        ),
        StructuredCitation(
            title="MCO 5216.20B Marine Corps Supplement to the DON Correspondence Manual",
            url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2795618/mco-521620b-wadmin-ch-4/",
            publisher="Headquarters Marine Corps",
            confidence=Confidence.low,
            notes="Manifest/source-note citation; verify current MCPEL status before final routing.",
        ),
    ]


def _warnings(request: CorrespondenceConversionRequest) -> list[str]:
    warnings = [
        *DEFAULT_WARNINGS,
        *detect_sensitive_input(" ".join([request.title, request.purpose, request.source_text, *request.constraints])),
        "Correspondence conversion is advisory only and requires human review before official routing or release.",
    ]
    return sorted(set(warnings))


def _follow_up_questions(request: CorrespondenceConversionRequest) -> list[str]:
    questions = [
        "What exact office, signer, or routing authority still needs confirmation?",
        "Which references or enclosures are mandatory versus optional?",
    ]
    if request.format_type == CorrespondenceFormatType.professional_email:
        questions.append("What response or action are you asking for, and by when?")
    else:
        questions.append("Does the receiving command expect a letter, memo, endorsement, or routing package?")
    return questions
