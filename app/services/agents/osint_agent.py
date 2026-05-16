from typing import Any

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    OSINT_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class OsintTrendAgent(Agent):
    metadata = AgentMetadata(
        id="osint-research-assistant",
        name="OSINT Research Assistant",
        description=(
            "Aggregates user-supplied trusted public-source news and social trend context into cited, "
            "counterargued, confidence-weighted assessments."
        ),
        domain="public-source research",
        intended_users=["staff officers", "civil affairs officers", "planners"],
        allowed_sources=[
            "official public releases",
            "trusted public news sources",
            "public academic or NGO reports",
            "public social media trend summaries where platform terms permit use",
            "CIA World Factbook for baseline country-reference context",
            "user-provided public URLs and local context summaries",
        ],
        disallowed_inputs=[
            "targeting requests",
            "private personal data",
            "classified collection",
            "credentialed or non-public data",
            "requests to bypass access controls, paywalls, CAPTCHAs, robots.txt, or rate limits",
            "unit movement tracking or operational inference",
        ],
        system_prompt=(
            "Aggregate trusted public-source information. Always cite supplied sources, provide "
            "counterarguments, distinguish facts from claims, and weigh confidence using source quality, "
            "corroboration, recency, and disagreement. Use the CIA World Factbook as a baseline public "
            "reference for country context before layering on current reporting."
        ),
        required_human_review=True,
        citation_required=True,
    )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        source_items = _extract_source_items(context.extra)
        citations = _citations_from_items(source_items)
        item_structured_citations = _structured_citations_from_items(source_items)

        answer = (
            "Public-source trend and evidence aggregation draft.\n\n"
            f"Research question:\n{input_text}\n\n"
            "Source handling:\n"
            f"{_format_sources(source_items)}\n\n"
            "Key claims and truth weighting:\n"
            f"{_format_claims(source_items)}\n\n"
            "Counterarguments and alternative explanations:\n"
            f"{_format_counterarguments(source_items)}\n\n"
            "Trend signals:\n"
            f"{_format_trends(source_items)}\n\n"
            "Gaps and next steps:\n"
            "- Use the CIA World Factbook as a baseline public reference when the question depends on country "
            "background, demographics, geography, infrastructure, or economy.\n"
            "- Add more independent public sources before treating any single-source claim as reliable.\n"
            "- Separate official statements, news reporting, and social trend signals in the final product.\n"
            "- Record retrieval timestamp, publisher, URL, and source type for every item.\n"
            "- Treat social media trends as noisy indicators, not validated facts.\n\n"
            "Recommended final output format:\n"
            "- Summary assessment\n"
            "- Claim table with confidence: high / medium / low / unknown\n"
            "- Supporting citations\n"
            "- Counterarguments\n"
            "- Source caveats and bias notes\n"
            "- Human-review decision points"
        )

        follow_ups = [
            "Which trusted public news sources should be included?",
            "Which social platforms or trend summaries are allowed by policy and terms of service?",
            "What time window defines recency for this question?",
            "Which claims should be verified before the summary is used?",
        ]
        warnings = [
            "Use topic-level trends only; do not track private individuals or collect private personal data.",
            "Do not bypass access controls, paywalls, CAPTCHAs, robots.txt, or rate limits.",
            "Social media trends are noisy and require corroboration before use.",
        ]
        response = self._response(
            answer=answer,
            input_text=input_text,
            follow_up_questions=follow_ups,
            citations=citation_titles(OSINT_REFERENCES)
            + (citations or ["No source URLs supplied; no factual claims are verified."]),
            structured_citations=[*structured_citations(OSINT_REFERENCES), *item_structured_citations],
            source_trust=source_trust_markers(
                OSINT_REFERENCES,
                notes_prefix="Use as baseline public-source grounding, then corroborate with current reporting.",
            ),
            confidence=_overall_confidence(source_items),
        )
        response.warnings.extend(warnings)
        return response


def build_osint_agent() -> OsintTrendAgent:
    return OsintTrendAgent()


def _extract_source_items(extra: dict[str, object]) -> list[dict[str, str]]:
    raw_items = extra.get("source_items", [])
    if not isinstance(raw_items, list):
        return []

    items: list[dict[str, str]] = []
    for raw_item in raw_items:
        if isinstance(raw_item, dict):
            item: dict[str, str] = {}
            for key, value in raw_item.items():
                if isinstance(key, str) and value is not None:
                    item[key] = str(value)
            if item:
                items.append(item)
    return items


def _citations_from_items(source_items: list[dict[str, str]]) -> list[str]:
    citations: list[str] = []
    for item in source_items:
        url = item.get("url")
        title = item.get("title", "Untitled source")
        publisher = item.get("publisher", "unknown publisher")
        if url:
            citations.append(f"{title} - {publisher} - {url}")
    return citations


def _structured_citations_from_items(source_items: list[dict[str, str]]) -> list[StructuredCitation]:
    structured: list[StructuredCitation] = []
    for item in source_items:
        url = item.get("url")
        if not url:
            continue
        structured.append(
            StructuredCitation(
                title=item.get("title", "Untitled source"),
                url=url,
                publisher=item.get("publisher"),
                retrieved_at=item.get("retrieved_at"),
                confidence=_item_confidence(item),
                notes=item.get("source_type"),
            )
        )
    return structured


def _format_sources(source_items: list[dict[str, str]]) -> str:
    if not source_items:
        return "- No trusted public source items supplied. Return a research plan, not an assessment."
    lines = []
    for item in source_items:
        title = item.get("title", "Untitled source")
        source_type = item.get("source_type", "unknown type")
        publisher = item.get("publisher", "unknown publisher")
        url = item.get("url", "missing URL")
        lines.append(f"- {title} ({source_type}, {publisher}): {url}")
    return "\n".join(lines)


def _format_claims(source_items: list[dict[str, str]]) -> str:
    if not source_items:
        return "- Unknown: no source-backed claims supplied."

    lines = []
    for item in source_items:
        claim = item.get("claim") or item.get("summary") or "Source requires claim extraction."
        confidence = _item_confidence(item)
        reason = _confidence_reason(item)
        lines.append(f"- Claim: {claim}\n  Assessment: {confidence.value}\n  Basis: {reason}")
    return "\n".join(lines)


def _format_counterarguments(source_items: list[dict[str, str]]) -> str:
    if not source_items:
        return "- Counterargument: the available evidence is insufficient to support a factual assessment."

    lines = []
    for item in source_items:
        counterargument = item.get("counterargument") or item.get("counterarguments")
        if not counterargument:
            counterargument = "Could reflect incomplete reporting, source bias, stale data, or platform amplification."
        lines.append(f"- {counterargument}")
    return "\n".join(lines)


def _format_trends(source_items: list[dict[str, str]]) -> str:
    if not source_items:
        return "- No trend signals supplied."

    lines = []
    for item in source_items:
        source_type = item.get("source_type", "unknown").lower()
        signal = item.get("trend_signal") or item.get("summary") or item.get("claim") or "No trend signal provided."
        weight = "low" if "social" in source_type else _item_confidence(item).value
        lines.append(f"- Signal: {signal}\n  Source type: {source_type}\n  Weight: {weight}")
    return "\n".join(lines)


def _overall_confidence(source_items: list[dict[str, str]]) -> Confidence:
    if not source_items:
        return Confidence.low
    if len(source_items) >= 3 and any(item.get("source_type", "").lower() == "official" for item in source_items):
        return Confidence.medium
    return Confidence.low


def _item_confidence(item: dict[str, str]) -> Confidence:
    source_type = item.get("source_type", "").lower()
    corroborated = item.get("corroborated", "").lower() in {"true", "yes", "1"}
    if source_type == "official" and corroborated:
        return Confidence.high
    if source_type in {"official", "news", "academic", "ngo"} or corroborated:
        return Confidence.medium
    return Confidence.low


def _confidence_reason(item: dict[str, Any]) -> str:
    source_type = str(item.get("source_type", "unknown"))
    recency = str(item.get("retrieved_at", "retrieval time not supplied"))
    corroborated = str(item.get("corroborated", "false"))
    return f"source_type={source_type}; retrieved_at={recency}; corroborated={corroborated}"
