from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, timedelta

from app.schemas.family_readiness import (
    FamilyReadinessChecklistItem,
    FamilyReadinessEvent,
    FamilyReadinessEventCreateRequest,
    FamilyReadinessGlossaryEntry,
    FamilyReadinessMilestone,
    ReadinessDurationBand,
    ReadinessItemCategory,
    ReadinessItemStatus,
)

DRAFT_FOOTER = "DRAFT — Verify all references against current official sources before acting."
DEERS_URL = "https://www.tricare.mil/DEERS"
MILCONNECT_URL = "https://www.tricare.mil/Plans/Eligibility/DEERS/milConnect"
RAPIDS_URL = "https://idco.dmdc.osd.mil/idco/"
DEPLOYMENT_URL = "https://planmydeployment.militaryonesource.mil/pre-deployment"
LEGAL_URL = (
    "https://planmydeployment.militaryonesource.mil/pre-deployment/service-members/"
    "legal-matters-steps-to-take-before-deployment/"
)

_BASELINE: tuple[tuple[ReadinessItemCategory, str, str, str | None], ...] = (
    (
        ReadinessItemCategory.administration,
        "Confirm the unit-provided readiness checklist",
        "Ask which unit requirements and deadlines apply to this absence.",
        None,
    ),
    (
        ReadinessItemCategory.contacts,
        "Record the unit readiness or family-support contact",
        "Keep the role and a public or user-approved contact method available to the household.",
        None,
    ),
    (
        ReadinessItemCategory.legal,
        "Schedule an installation legal-assistance review",
        "A qualified provider should review legal readiness; this app does not draft legal documents.",
        LEGAL_URL,
    ),
    (
        ReadinessItemCategory.legal,
        "Review whether a limited or special power of attorney is needed",
        "Ask legal assistance and affected institutions what form and scope they require.",
        LEGAL_URL,
    ),
    (
        ReadinessItemCategory.legal,
        "Review wills, emergency data, beneficiaries, and document access",
        "Confirm current records without storing their sensitive contents here.",
        LEGAL_URL,
    ),
    (
        ReadinessItemCategory.deers,
        "Review DEERS contact information",
        "Confirm address, email, and phone information through official DEERS channels.",
        DEERS_URL,
    ),
    (
        ReadinessItemCategory.deers,
        "Check dependent ID-card expiration dates",
        "Use the RAPIDS locator if an eligible family member needs an ID-card action.",
        RAPIDS_URL,
    ),
    (
        ReadinessItemCategory.household,
        "Review recurring household responsibilities",
        "Agree who will handle bills, vehicles, housing, pets, mail, and urgent repairs without recording credentials.",
        None,
    ),
    (
        ReadinessItemCategory.contacts,
        "Validate emergency contacts and backup support",
        "Make sure the household knows who to call if the primary contact is unavailable.",
        None,
    ),
    (
        ReadinessItemCategory.opsec,
        "Agree on a communication rhythm and backup method",
        "Set expectations without sharing mission or movement details.",
        DEPLOYMENT_URL,
    ),
    (
        ReadinessItemCategory.opsec,
        "Review family OPSEC reminders",
        "Do not publish exact dates, routes, locations, missions, or information showing a household is unattended.",
        DEPLOYMENT_URL,
    ),
    (
        ReadinessItemCategory.family_support,
        "Review child, pet, school, employer, caregiver, or special-support coordination",
        "Mark relevant categories while keeping names, diagnoses, and custody details outside this checklist.",
        DEPLOYMENT_URL,
    ),
)


def select_duration_band(start: date | None, end: date | None) -> ReadinessDurationBand:
    if start is None or end is None:
        return ReadinessDurationBand.custom
    days = (end - start).days + 1
    if 14 <= days <= 30:
        return ReadinessDurationBand.short
    if days <= 180:
        return ReadinessDurationBand.medium
    if days <= 395:
        return ReadinessDurationBand.long
    return ReadinessDurationBand.custom


def build_event(request: FamilyReadinessEventCreateRequest) -> FamilyReadinessEvent:
    now = datetime.now(UTC)
    band = request.duration_band or select_duration_band(request.approximate_start, request.approximate_end)
    items = [_item(*definition) for definition in _BASELINE]
    if band is ReadinessDurationBand.long:
        items.extend(
            [
                _item(
                    ReadinessItemCategory.reintegration,
                    "Plan a household reintegration review",
                    "Revisit responsibilities, expectations, benefits contacts, and legal access arrangements after return.",
                    DEPLOYMENT_URL,
                    origin="duration",
                ),
                _item(
                    ReadinessItemCategory.household,
                    "Identify mid-absence household check-ins",
                    "Choose a practical rhythm for reviewing household issues without operational details.",
                    DEPLOYMENT_URL,
                    origin="duration",
                ),
            ]
        )
    return FamilyReadinessEvent(
        event_id=secrets.token_hex(10),
        user_key=request.user_key,
        title=request.title.strip(),
        approximate_start=request.approximate_start,
        approximate_end=request.approximate_end,
        duration_band=band,
        items=items,
        milestones=_milestones(request.approximate_start, request.approximate_end),
        glossary=_baseline_glossary(),
        is_demo=request.is_demo,
        created_at=now,
        updated_at=now,
    )


def render_spouse_summary(event: FamilyReadinessEvent) -> str:
    tasks = [
        f"- [{'x' if item.status is ReadinessItemStatus.complete else ' '}] {item.task}"
        for item in event.items
        if item.shareable
    ]
    contacts = [
        f"- {item.role}: {' · '.join(value for value in [item.organization, item.phone, item.email] if value)}"
        for item in event.contacts
        if item.shareable
    ]
    terms = [
        f"- **{item.term} — {item.expansion}:** {item.plain_language}" for item in event.glossary if item.shareable
    ]
    milestones = [f"- {item.target_date.isoformat()}: {item.title}" for item in event.milestones]
    window = _window_label(event)
    return "\n".join(
        [
            f"# {event.title}",
            "",
            f"Approximate absence window: {window}",
            "",
            "## Readiness checklist",
            *(tasks or ["- No shareable checklist items selected."]),
            "",
            "## Contacts",
            *(contacts or ["- Add unit and support contacts before sharing."]),
            "",
            "## Rough milestones",
            *(milestones or ["- Add an approximate start window to generate milestones."]),
            "",
            "## Plain-language guide",
            *terms,
            "",
            DRAFT_FOOTER,
        ]
    )


def _item(
    category: ReadinessItemCategory, task: str, plain: str, source_url: str | None, *, origin: str = "baseline"
) -> FamilyReadinessChecklistItem:
    return FamilyReadinessChecklistItem(
        item_id=secrets.token_hex(8),
        category=category,
        task=task,
        plain_language=plain,
        source_url=source_url,
        origin=origin,
    )


def _milestones(start: date | None, end: date | None) -> list[FamilyReadinessMilestone]:
    if start is None:
        return []
    definitions = (
        (90, "T-90", "Start legal and household readiness review"),
        (60, "T-60", "Review DEERS contact information"),
        (30, "T-30", "Validate contacts and household continuity"),
        (14, "T-14", "Review communication rhythm and OPSEC"),
        (7, "T-7", "Complete final personal-readiness check"),
    )
    result = [
        FamilyReadinessMilestone(
            milestone_id=secrets.token_hex(8), label=label, title=title, target_date=start - timedelta(days=offset)
        )
        for offset, label, title in definitions
    ]
    if end:
        result.append(
            FamilyReadinessMilestone(
                milestone_id=secrets.token_hex(8),
                label="Return window",
                title="Begin household reintegration review",
                target_date=end,
            )
        )
    return result


def _baseline_glossary() -> list[FamilyReadinessGlossaryEntry]:
    definitions = (
        ("AT", "Annual Training", "A scheduled period of active-duty training for a reserve member."),
        (
            "DEERS",
            "Defense Enrollment Eligibility Reporting System",
            "The Defense Department eligibility record used for benefits such as TRICARE.",
        ),
        (
            "RAPIDS",
            "Real-Time Automated Personnel Identification System",
            "The ID-card office system and locator used for military identification-card services.",
        ),
        (
            "POA",
            "Power of Attorney",
            "A legal document prepared or reviewed with qualified legal assistance that authorizes another person to act in defined matters.",
        ),
        (
            "OPSEC",
            "Operations Security",
            "Practices that protect sensitive details such as exact dates, locations, routes, and mission information.",
        ),
        (
            "milConnect",
            "milConnect",
            "An official online service for selected personnel, benefits, and DEERS-related actions.",
        ),
    )
    return [
        FamilyReadinessGlossaryEntry(term=term, expansion=expansion, plain_language=plain)
        for term, expansion, plain in definitions
    ]


def _window_label(event: FamilyReadinessEvent) -> str:
    if event.approximate_start and event.approximate_end:
        return f"{event.approximate_start.isoformat()} through {event.approximate_end.isoformat()}"
    if event.approximate_start:
        return f"Beginning around {event.approximate_start.isoformat()}"
    return "Not set"
