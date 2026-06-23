from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.custom_mos_recipe import (
    CustomMosRecipe,
    CustomMosRecipeCreateRequest,
    CustomMosRecipeListResponse,
)
from app.services.agents.registry import agent_registry
from app.services.staff.custom_mos_store import CustomMosRecipeStoreService

router = APIRouter(
    prefix="/custom-mos-recipes",
    tags=["custom-mos-recipes"],
    dependencies=[LocalApiKeyDependency],
)

VALID_PARENT_AGENTS = {
    "staff-s1",
    "staff-s2",
    "staff-opso",
    "staff-s4",
    "staff-s6",
    "staff-sel",
    "staff-surgeon",
    "staff-sja",
    "staff-pao",
    "staff-chaplain",
    "staff-provost",
    "staff-ig",
    "staff-g8",
    "staff-g9",
    "staff-xo",
    "staff-battle_captain",
    "ace",
    "gce",
    "lce",
    "infantry-tactics-advisor",
    "fires-advisor",
    "chief-of-staff",
    "orm-risk-management",
}


def _get_store() -> Iterator[CustomMosRecipeStoreService]:
    settings = get_settings()
    yield CustomMosRecipeStoreService(settings.custom_mos_recipes_storage_dir)


@router.get("/{user_key}", response_model=CustomMosRecipeListResponse)
def list_recipes(
    user_key: str,
    store: Annotated[CustomMosRecipeStoreService, Depends(_get_store)],
) -> CustomMosRecipeListResponse:
    recipes = store.get(user_key)
    return CustomMosRecipeListResponse(recipes=recipes, message=f"{len(recipes)} custom MOS recipe(s).")


@router.post("/{user_key}", response_model=CustomMosRecipeListResponse)
def create_recipe(
    user_key: str,
    request: CustomMosRecipeCreateRequest,
    store: Annotated[CustomMosRecipeStoreService, Depends(_get_store)],
) -> CustomMosRecipeListResponse:
    if request.parent_agent not in VALID_PARENT_AGENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parent_agent '{request.parent_agent}'. Must be one of: {sorted(VALID_PARENT_AGENTS)}",
        )
    if agent_registry.get(request.parent_agent) is None:
        raise HTTPException(status_code=400, detail=f"Parent agent '{request.parent_agent}' is not registered.")
    recipe = CustomMosRecipe(
        mos_code=request.mos_code.strip(),
        title=request.title.strip(),
        parent_agent=request.parent_agent,
        focus_areas=[fa.strip() for fa in request.focus_areas if fa.strip()],
        starter_prompt=request.starter_prompt.strip(),
    )
    recipes = store.add(user_key, recipe)
    return CustomMosRecipeListResponse(recipes=recipes, message=f"Saved custom MOS recipe for {recipe.mos_code}.")


@router.delete("/{user_key}/{mos_code}", response_model=CustomMosRecipeListResponse)
def delete_recipe(
    user_key: str,
    mos_code: str,
    store: Annotated[CustomMosRecipeStoreService, Depends(_get_store)],
) -> CustomMosRecipeListResponse:
    recipes = store.delete(user_key, mos_code)
    return CustomMosRecipeListResponse(recipes=recipes, message=f"Deleted custom MOS recipe for {mos_code}.")
