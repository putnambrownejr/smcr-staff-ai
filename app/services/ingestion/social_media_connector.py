import hashlib
from datetime import UTC, datetime
from urllib.parse import urlparse

from app.schemas.social import (
    SocialIngestRequest,
    SocialIngestResponse,
    SocialSourceType,
    SocialTrendInput,
    SocialTrendRecord,
    VettedSocialSource,
)

DEFAULT_SOCIAL_WARNINGS = [
    "Use only public, lawfully accessible content or platform-approved exports/APIs.",
    "Do not collect private personal data, bypass access controls, evade rate limits, or track private individuals.",
    "Social media trends are noisy indicators and require corroboration before use.",
]

VETTED_SOURCES: tuple[VettedSocialSource, ...] = (
    VettedSocialSource(
        id="official-public",
        name="Official public websites and feeds",
        source_type=SocialSourceType.official,
        base_url="*.mil, *.gov, official public affairs sites",
        allowed_collection="Public releases, RSS feeds, public pages, and official posts.",
        prohibited_collection=["Authenticated content", "non-public records", "CUI or classified material"],
    ),
    VettedSocialSource(
        id="trusted-news",
        name="Trusted public news sources",
        source_type=SocialSourceType.news,
        base_url="publisher websites and RSS feeds",
        allowed_collection="Public articles, RSS entries, and article metadata.",
        prohibited_collection=["Paywall bypass", "credentialed content", "bulk personal data collection"],
    ),
    VettedSocialSource(
        id="public-social-trends",
        name="Public social media trend summaries",
        source_type=SocialSourceType.social_trend,
        base_url="platform-approved public URLs, exports, or APIs",
        allowed_collection="Topic-level public trend summaries, post URLs, public metrics when terms permit.",
        prohibited_collection=[
            "Private profiles",
            "direct messages",
            "doxxing",
            "individual tracking",
            "CAPTCHA or rate-limit bypass",
        ],
    ),
)

BLOCKED_HOST_FRAGMENTS = (
    "localhost",
    "127.0.0.1",
    "10.",
    "172.16.",
    "192.168.",
)


class SocialMediaVettedConnector:
    """Normalizes vetted public social/news trend inputs for OSINT source evaluation.

    This connector accepts already collected public records. Live platform API clients
    should be added as explicit adapters with their own terms, rate-limit, and auth review.
    """

    def vetted_sources(self) -> list[VettedSocialSource]:
        return list(VETTED_SOURCES)

    def ingest(self, request: SocialIngestRequest) -> SocialIngestResponse:
        records: list[SocialTrendRecord] = []
        warnings = [*DEFAULT_SOCIAL_WARNINGS]
        for item in request.records:
            item_warnings = self._validate_item(item, strict=request.strict_vetting)
            if request.strict_vetting and item_warnings:
                warnings.extend(item_warnings)
                continue
            records.append(_normalize_record(item, item_warnings))

        return SocialIngestResponse(
            accepted=True,
            records_seen=len(request.records),
            records_accepted=len(records),
            records=records,
            osint_source_items=[to_osint_source_item(record) for record in records],
            warnings=warnings,
        )

    def _validate_item(self, item: SocialTrendInput, strict: bool) -> list[str]:
        warnings: list[str] = []
        parsed = urlparse(str(item.url))
        if parsed.scheme not in {"http", "https"}:
            warnings.append(f"Unsupported URL scheme for {item.url}.")
        if any(parsed.hostname and parsed.hostname.startswith(fragment) for fragment in BLOCKED_HOST_FRAGMENTS):
            warnings.append(f"Private or local URL is not allowed for social trend ingestion: {item.url}.")
        if item.source_type == SocialSourceType.social_trend and not item.trend_signal:
            warnings.append("Social trend records should include a topic-level trend_signal.")
        if _looks_person_targeted(item) and strict:
            warnings.append("Record appears person-targeted. Use topic-level trends only.")
        return warnings


def to_osint_source_item(record: SocialTrendRecord) -> dict[str, str]:
    return {
        "title": record.title,
        "publisher": record.publisher,
        "source_type": record.source_type.value,
        "url": record.url,
        "summary": record.summary,
        "claim": record.claim or "",
        "trend_signal": record.trend_signal or "",
        "counterargument": record.counterargument or "",
        "corroborated": str(record.corroborated).lower(),
        "retrieved_at": record.retrieved_at.isoformat(),
    }


def _normalize_record(item: SocialTrendInput, warnings: list[str]) -> SocialTrendRecord:
    retrieved_at = item.retrieved_at or datetime.now(UTC)
    source_id = hashlib.sha256(f"{item.url}|{item.summary}|{retrieved_at.isoformat()}".encode()).hexdigest()[:16]
    return SocialTrendRecord(
        source_id=source_id,
        title=item.title,
        url=str(item.url),
        publisher=item.publisher,
        source_type=item.source_type,
        platform=item.platform,
        author_or_channel=item.author_or_channel,
        published_at=item.published_at,
        retrieved_at=retrieved_at,
        summary=item.summary,
        claim=item.claim,
        trend_signal=item.trend_signal,
        counterargument=item.counterargument,
        corroborated=item.corroborated,
        tags=item.tags,
        warnings=warnings,
    )


def _looks_person_targeted(item: SocialTrendInput) -> bool:
    text = " ".join([item.title, item.summary, item.claim or "", item.trend_signal or ""]).lower()
    person_targeting_terms = ("home address", "phone number", "personal email", "dox", "private profile")
    return any(term in text for term in person_targeting_terms)
