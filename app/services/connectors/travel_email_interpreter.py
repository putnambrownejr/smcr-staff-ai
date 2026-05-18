from __future__ import annotations

import re
from datetime import date, timedelta

from app.schemas.chief import ChiefActionItem
from app.schemas.connector_digest import ConnectorMessageSummary, TravelEmailCaseSummary

DATE_PATTERN = re.compile(r"\b(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{2,4})\b")


def build_travel_cases(messages: list[ConnectorMessageSummary]) -> list[TravelEmailCaseSummary]:
    cases: list[TravelEmailCaseSummary] = []
    for message in messages:
        case = _case_from_message(message)
        if case is not None:
            cases.append(case)
    return cases


def action_items_from_travel_cases(cases: list[TravelEmailCaseSummary]) -> list[ChiefActionItem]:
    items: list[ChiefActionItem] = []
    for case in cases:
        if case.voucher_due_date is not None:
            items.append(
                ChiefActionItem(
                    title=f"Travel voucher due: {case.title}",
                    category="travel",
                    priority=_voucher_priority(case.travel_status),
                    due_date=case.voucher_due_date,
                    source="connector_travel_case",
                    recommendation=(
                        "Close the voucher NLT five days after travel end, confirm receipts are complete, "
                        "and resolve any DTS gaps before this slips."
                    ),
                )
            )
        if case.receipts_to_collect:
            items.append(
                ChiefActionItem(
                    title=f"Collect travel receipts: {case.title}",
                    category="travel",
                    priority="medium",
                    due_date=case.travel_end,
                    source="connector_travel_case",
                    recommendation=(
                        "Collect and store the required receipts locally so voucher support does not become "
                        "a post-travel scramble."
                    ),
                )
            )
        if case.rental_car_expected:
            items.append(
                ChiefActionItem(
                    title=f"Verify rental-car support: {case.title}",
                    category="travel",
                    priority="medium",
                    due_date=case.travel_start,
                    source="connector_travel_case",
                    recommendation=(
                        "Confirm rental-car reservation details, pickup/dropoff timing, and required receipt "
                        "capture before travel starts."
                    ),
                )
            )
    return items


def handoff_lines_from_travel_cases(cases: list[TravelEmailCaseSummary]) -> list[str]:
    lines: list[str] = []
    for case in cases:
        if case.travel_start is not None or case.travel_end is not None:
            lines.append(
                "Admin watch: "
                f"{case.title} travel window "
                f"{case.travel_start or 'unknown start'} to {case.travel_end or 'unknown end'}."
            )
        if case.voucher_due_date is not None:
            lines.append(f"Admin watch: {case.title} voucher due NLT {case.voucher_due_date.isoformat()}.")
        if case.rental_car_expected:
            lines.append(f"Admin watch: {case.title} includes rental-car follow-through and receipt capture.")
    return lines


def _case_from_message(message: ConnectorMessageSummary) -> TravelEmailCaseSummary | None:
    text = " ".join(
        part
        for part in [
            message.subject,
            message.sender or "",
            message.action_hint or "",
            message.notes or "",
            message.body_preview or "",
        ]
        if part
    )
    lowered = text.lower()
    if not any(token in lowered for token in ("dts", "travel", "ci travel", "itinerary", "rental car", "voucher")):
        return None

    dates = _extract_dates(text)
    travel_start = dates[0] if dates else None
    travel_end = dates[1] if len(dates) > 1 else dates[0] if len(dates) == 1 else None
    rental_car_expected = any(token in lowered for token in ("rental car", "enterprise", "hertz", "avis", "budget"))

    confidence_notes: list[str] = []
    if travel_start is None:
        confidence_notes.append("Travel start date was not confidently extracted from the message summary.")
    if travel_end is None:
        confidence_notes.append("Travel end date was not confidently extracted from the message summary.")

    status = _travel_status(lowered, message)
    voucher_due_date = travel_end + timedelta(days=5) if travel_end is not None else None
    receipts_to_collect = _receipt_requirements(rental_car_expected)

    recommendations = [
        "Cross-check the summarized email against DTS and CI Travel before acting on it.",
    ]
    if voucher_due_date is not None:
        recommendations.append(
            f"Set a voucher suspense no later than {voucher_due_date.isoformat()} if the travel actually completed."
        )
    if receipts_to_collect:
        recommendations.append("Collect required receipts locally before the traveler disperses.")

    return TravelEmailCaseSummary(
        title=_case_title(message.subject),
        source_subject=message.subject,
        sender=message.sender,
        travel_status=status,
        travel_start=travel_start,
        travel_end=travel_end,
        voucher_due_date=voucher_due_date,
        rental_car_expected=rental_car_expected,
        receipts_to_collect=receipts_to_collect,
        confidence_notes=confidence_notes,
        recommendations=recommendations,
    )


def _extract_dates(text: str) -> list[date]:
    dates = []
    for match in DATE_PATTERN.finditer(text):
        month = int(match.group("month"))
        day = int(match.group("day"))
        year = int(match.group("year"))
        if year < 100:
            year += 2000
        try:
            dates.append(date(year, month, day))
        except ValueError:
            continue
    deduped = []
    seen = set()
    for item in dates:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _travel_status(lowered: str, message: ConnectorMessageSummary) -> str:
    if "voucher" in lowered:
        return "post_travel"
    if any(token in lowered for token in ("ticketed", "itinerary", "reservation confirmed", "ci travel")):
        return "upcoming_travel"
    if "receipt" in lowered:
        return "post_travel"
    if message.received_at:
        return "watch"
    return "watch"


def _receipt_requirements(rental_car_expected: bool) -> list[str]:
    items = ["lodging", "airfare or ticketed itinerary"]
    if rental_car_expected:
        items.append("rental car")
        items.append("fuel if applicable")
    return items


def _voucher_priority(status: str) -> str:
    if status == "post_travel":
        return "high"
    return "medium"


def _case_title(subject: str) -> str:
    title = subject.strip()
    if len(title) <= 72:
        return title
    return title[:69] + "..."
