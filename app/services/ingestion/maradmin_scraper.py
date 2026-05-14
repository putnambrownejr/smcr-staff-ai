import hashlib
import re

from app.schemas.ingestion import MessageRecord
from app.services.ingestion.rss_client import FeedItem

TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Reserve": ("reserve", "smcr", "marforres"),
    "Officer": ("officer", "warrant"),
    "Promotion": ("promotion", "selection board"),
    "PME": ("pme", "professional military education"),
    "Uniform": ("uniform", "grooming"),
    "Training": ("training", "school", "course"),
    "Mobilization": ("mobilization", "activation"),
    "Admin": ("admin", "administrative"),
    "Travel": ("travel", "dts", "tdy"),
    "Pay": ("pay", "allowance"),
    "Fitness": ("pft", "cft", "fitness"),
    "Awards": ("award", "decoration"),
    "Safety": ("safety", "risk"),
    "Doctrine": ("doctrine", "publication", "order", "mcdp", "mcwp", "mctp", "mcrp"),
    "DocumentUpdate": (
        "revision",
        "revised",
        "change",
        "update",
        "updated",
        "published",
        "effective",
        "cancel",
        "canceled",
        "cancelled",
        "supersede",
        "superseded",
        "mcpel",
        "mcramm",
        "5216.20",
        "5216.5",
        "1020.34",
        "1610.7",
    ),
}


def tag_message(item: FeedItem) -> list[str]:
    haystack = f"{item.title} {item.summary or ''}".lower()
    tags = [tag for tag, keywords in TAG_KEYWORDS.items() if any(keyword in haystack for keyword in keywords)]
    return tags or ["Admin"]


def normalize_messages(items: list[FeedItem]) -> list[dict[str, object]]:
    return [
        {
            "title": item.title,
            "link": item.link,
            "published_at": item.published_at,
            "summary": item.summary,
            "tags": tag_message(item),
        }
        for item in items
    ]


def normalize_message_records(items: list[FeedItem]) -> list[MessageRecord]:
    return [message_record_from_feed_item(item) for item in items]


def message_record_from_feed_item(item: FeedItem) -> MessageRecord:
    message_number, fiscal_year = _parse_message_number(item.title)
    source_id = message_number or hashlib.sha256(item.link.encode("utf-8")).hexdigest()[:16]
    source_hash = hashlib.sha256(f"{item.title}\n{item.link}\n{item.summary or ''}".encode()).hexdigest()
    warnings = []
    if message_number is None:
        warnings.append("Could not parse MARADMIN message number from title.")
    return MessageRecord(
        source_id=f"maradmin-{source_id.lower()}",
        title=item.title,
        canonical_url=item.link,
        message_number=message_number,
        fiscal_year=fiscal_year,
        published_at=item.published_at,
        summary=item.summary,
        tags=tag_message(item),
        source_hash=source_hash,
        parser_warnings=warnings,
    )


def _parse_message_number(title: str) -> tuple[str | None, int | None]:
    match = re.search(r"\b(?P<number>\d{3})/(?P<year>\d{2})\b", title)
    if match is None:
        return None, None
    year = int(match.group("year"))
    fiscal_year = 2000 + year if year < 80 else 1900 + year
    return match.group(0), fiscal_year
