from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.user_profile import UserProfile, UserProfileResponse, UserProfileUpsertRequest
from app.services.staff.billet_research_service import build_research_note
from app.services.staff.billet_research_store import BilletResearchStore
from app.services.staff.user_profile_store import UserProfileStore

router = APIRouter(prefix="/user-profile", tags=["user profile"], dependencies=[LocalApiKeyDependency])


def get_user_profile_store() -> Iterator[UserProfileStore]:
    settings = get_settings()
    yield UserProfileStore(settings.user_profile_storage_dir)


def get_billet_research_store() -> Iterator[BilletResearchStore]:
    settings = get_settings()
    yield BilletResearchStore(settings.billet_research_storage_dir)


@router.get("/{user_key}", response_model=UserProfile)
def get_user_profile(
    user_key: str,
    store: Annotated[UserProfileStore, Depends(get_user_profile_store)],
) -> UserProfile:
    profile = store.get(user_key)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No profile stored for {user_key}.")
    return profile


@router.put("/{user_key}", response_model=UserProfileResponse)
def upsert_user_profile(
    user_key: str,
    request: UserProfileUpsertRequest,
    store: Annotated[UserProfileStore, Depends(get_user_profile_store)],
) -> UserProfileResponse:
    try:
        profile = store.upsert(
            user_key,
            billet=request.billet,
            unit=request.unit,
            mos=request.mos,
            format_preference=request.format_preference,
            one_number_one_rule=request.one_number_one_rule,
            style_notes=request.style_notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return UserProfileResponse(profile=profile, message="Profile saved.")


@router.delete("/{user_key}", status_code=204)
def delete_user_profile(
    user_key: str,
    store: Annotated[UserProfileStore, Depends(get_user_profile_store)],
) -> None:
    store.delete(user_key)


@router.get("/{user_key}/research", response_class=PlainTextResponse)
def get_billet_research(
    user_key: str,
    research_store: Annotated[BilletResearchStore, Depends(get_billet_research_store)],
) -> str:
    note = research_store.get(user_key)
    if note is None:
        raise HTTPException(status_code=404, detail="No billet research stored for this user.")
    return note


@router.post("/{user_key}/research", response_class=PlainTextResponse)
def generate_billet_research(
    user_key: str,
    profile_store: Annotated[UserProfileStore, Depends(get_user_profile_store)],
    research_store: Annotated[BilletResearchStore, Depends(get_billet_research_store)],
) -> str:
    profile = profile_store.get(user_key)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No profile stored for {user_key}.")
    if not any([profile.billet, profile.unit, profile.mos]):
        raise HTTPException(status_code=422, detail="Profile must have at least one of: billet, unit, or MOS set.")
    note = build_research_note(user_key, profile.billet, profile.unit, profile.mos)
    research_store.upsert(user_key, note)
    return note
