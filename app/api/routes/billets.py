import httpx
from fastapi import APIRouter, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.schemas.billets import BilletSearchRequest, BilletSearchResponse, BilletSourceInfo
from app.services.billets.recommender import DEFAULT_BILLET_WARNINGS, recommend_billets
from app.services.ingestion.smcr_bic_scraper import OFFICIAL_BILLET_SOURCE_URLS, SmcrBicScraper, official_billet_sources

router = APIRouter(prefix="/billets", tags=["SMCR billets"], dependencies=[LocalApiKeyDependency])


@router.get("/sources", response_model=list[BilletSourceInfo])
def list_billet_sources() -> list[BilletSourceInfo]:
    return official_billet_sources()


@router.post("/recommend", response_model=BilletSearchResponse)
async def recommend_smcr_billets(request: BilletSearchRequest) -> BilletSearchResponse:
    source_url = OFFICIAL_BILLET_SOURCE_URLS[request.source_key.value]
    scraper = SmcrBicScraper()
    try:
        html = await scraper.fetch_html(source_url)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Timed out fetching official billet source.") from exc
    except httpx.HTTPStatusError as exc:
        detail = f"Official billet source returned {exc.response.status_code}."
        raise HTTPException(status_code=502, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not fetch official billet source.") from exc
    billets, discovered_links = scraper.parse(html, source_url)
    source = BilletSourceInfo(
        name="Requested public Marine Corps billet source",
        url=source_url,
        description="Live public-source scrape for open SMCR/Reserve billet information where available.",
        warnings=DEFAULT_BILLET_WARNINGS,
    )
    return BilletSearchResponse(
        source=source,
        discovered_links=discovered_links,
        billets_seen=len(billets),
        recommendations=recommend_billets(billets, request.profile, request.max_results),
        warnings=[
            *DEFAULT_BILLET_WARNINGS,
            "If the official page only launches Reserve Hub, use the discovered link to complete a live search.",
            "Do not enter sensitive personal data into this prototype.",
        ],
    )
