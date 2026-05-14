from app.schemas.billets import BilletRecommendation, BilletUserProfile, SmcrBillet

DEFAULT_BILLET_WARNINGS = [
    "Public billet data can change quickly. Verify availability through official Marine Corps Reserve channels.",
    "Recommendations are advisory only and do not determine eligibility, assignment, or approval.",
]

RANK_EQUIVALENTS: dict[str, set[str]] = {
    "O1": {"O1", "2NDLT", "SECOND LIEUTENANT"},
    "O2": {"O2", "1STLT", "FIRST LIEUTENANT"},
    "O3": {"O3", "CAPT", "CAPTAIN"},
    "O4": {"O4", "MAJ", "MAJOR"},
    "O5": {"O5", "LTCOL", "LIEUTENANT COLONEL"},
    "O6": {"O6", "COL", "COLONEL"},
    "E3": {"E3", "LCPL", "LANCE CORPORAL"},
    "E4": {"E4", "CPL", "CORPORAL"},
    "E5": {"E5", "SGT", "SERGEANT"},
    "E6": {"E6", "SSGT", "STAFF SERGEANT"},
    "E7": {"E7", "GYSGT", "GUNNERY SERGEANT"},
    "E8": {"E8", "MSGT", "1STSGT", "MASTER SERGEANT", "FIRST SERGEANT"},
    "E9": {"E9", "MGYSGT", "SGTMAJ", "MASTER GUNNERY SERGEANT", "SERGEANT MAJOR"},
}


def recommend_billets(
    billets: list[SmcrBillet],
    profile: BilletUserProfile,
    max_results: int = 10,
) -> list[BilletRecommendation]:
    recommendations = [_score_billet(billet, profile) for billet in billets]
    recommendations.sort(key=lambda item: item.score, reverse=True)
    return [item for item in recommendations if item.score > 0][:max_results]


def _score_billet(billet: SmcrBillet, profile: BilletUserProfile) -> BilletRecommendation:
    score = 0
    reasons: list[str] = []

    if profile.mos and billet.mos:
        billet_mos = billet.mos.strip()
        if profile.mos == billet_mos:
            score += 50
            reasons.append(f"MOS match: {profile.mos}")
        elif billet_mos in {"8006", "8007", "8014", "8040", "8059", "9907", "9914", "9960"}:
            score += 15
            reasons.append(f"Billet MOS {billet_mos} may be broad/open by policy or notes; verify eligibility.")

    if profile.rank and _rank_matches(profile.rank, billet):
        score += 30
        reasons.append("Rank appears compatible with billet rank/range.")

    location_text = (billet.location or "").lower()
    for desired_location in profile.desired_locations:
        if desired_location.lower() in location_text:
            score += 20
            reasons.append(f"Location match: {desired_location}")
            break

    searchable_text = " ".join(
        item or ""
        for item in [
            billet.title,
            billet.unit,
            billet.location,
            billet.notes,
            billet.mos,
        ]
    ).lower()
    for keyword in profile.keywords:
        if keyword.lower() in searchable_text:
            score += 10
            reasons.append(f"Keyword match: {keyword}")

    if profile.willing_to_travel and billet.location:
        score += 3
        reasons.append("User is willing to travel; location remains a human-review factor.")

    return BilletRecommendation(
        billet=billet,
        score=score,
        match_reasons=reasons or ["Low-confidence lexical match only."],
        warnings=DEFAULT_BILLET_WARNINGS,
    )


def _rank_matches(profile_rank: str, billet: SmcrBillet) -> bool:
    profile_tokens = _rank_tokens(profile_rank)
    billet_ranks = [billet.rank, billet.rank_min, billet.rank_max]
    billet_tokens = set().union(*[_rank_tokens(rank) for rank in billet_ranks if rank])
    return bool(profile_tokens.intersection(billet_tokens))


def _rank_tokens(rank: str) -> set[str]:
    normalized = rank.upper().replace("-", "").replace(" ", "")
    tokens = {normalized}
    for grade, equivalents in RANK_EQUIVALENTS.items():
        compact_equivalents = {value.replace(" ", "") for value in equivalents}
        if normalized == grade or normalized in compact_equivalents:
            tokens.update(compact_equivalents)
            tokens.add(grade)
    return tokens
