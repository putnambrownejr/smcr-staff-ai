from app.core.security import DEFAULT_WARNINGS
from app.schemas.agents import Confidence
from app.schemas.staff import S2EstimateRequest, S2EstimateResponse


class S2Estimator:
    def build(self, request: S2EstimateRequest) -> S2EstimateResponse:
        summary_assessment = [
            f"Question: {request.question}",
            "Treat this as a public-source estimate for planning support, not authoritative intelligence.",
            "Separate corroborated public reporting from noisy social or single-source claims.",
        ]
        if request.audience:
            summary_assessment.append(f"Supported audience / consumer: {request.audience}")
        if request.timeframe:
            summary_assessment.append(f"Timeframe / recency window: {request.timeframe}")

        assessed_claims = []
        source_caveats = []
        for item in request.source_items[:8]:
            title = item.get("title", "Untitled source")
            claim = item.get("claim") or item.get("summary") or "Source requires claim extraction."
            source_type = item.get("source_type", "unknown")
            corroborated = str(item.get("corroborated", "false")).lower() in {"true", "1", "yes"}
            confidence = _confidence(source_type, corroborated)
            assessed_claims.append(f"{title}: {claim} (confidence: {confidence.value})")
            source_caveats.append(
                f"{title}: source_type={source_type}; corroborated={str(corroborated).lower()}; verify before use."
            )
        if not assessed_claims:
            assessed_claims.append(
                "No public source items were supplied; provide source-backed material "
                "before using this estimate."
            )

        collection_gaps = [
            "What claims still rest on a single source?",
            "What official public source could confirm or contradict the current picture?",
            "What assumption would change the plan most if it proves wrong?",
        ]
        if not request.source_items:
            collection_gaps.append(
                "Add official releases, trusted news, or vetted social-trend summaries "
                "before briefing this."
            )

        command_considerations = [
            "Brief what is known, what is assumed, and what remains unknown.",
            "Flag any claim that should not drive a decision until corroborated.",
            "Treat public social-trend signals as context, not as validated facts.",
            "Update the estimate when a better public source or official release appears.",
        ]

        return S2EstimateResponse(
            title=f"S-2 estimate: {request.title}",
            summary_assessment=summary_assessment,
            assessed_claims=assessed_claims,
            collection_gaps=collection_gaps,
            command_considerations=command_considerations,
            source_caveats=source_caveats,
            warnings=[
                *DEFAULT_WARNINGS,
                "S-2 estimate support is advisory only and limited to public, lawfully accessible source material.",
            ],
        )


def _confidence(source_type: str, corroborated: bool) -> Confidence:
    normalized = source_type.lower()
    if normalized == "official" and corroborated:
        return Confidence.high
    if normalized in {"official", "news", "academic", "ngo"} or corroborated:
        return Confidence.medium
    return Confidence.low
