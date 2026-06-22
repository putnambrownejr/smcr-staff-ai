from datetime import datetime

from pydantic import BaseModel, Field


class CustomMosRecipe(BaseModel):
    mos_code: str = Field(min_length=2, max_length=10, description="MOS code, e.g. '0602' or '1302'")
    title: str = Field(min_length=2, max_length=120, description="Short title, e.g. 'Communications Officer'")
    parent_agent: str = Field(description="Agent ID of the parent staff archetype to route through")
    focus_areas: list[str] = Field(
        min_length=1,
        max_length=8,
        description="Key focus areas for this MOS, e.g. ['PACE planning', 'crypto accountability']",
    )
    starter_prompt: str = Field(
        default="",
        max_length=500,
        description="Optional default starter prompt for this MOS lane",
    )


class CustomMosRecipeStore(BaseModel):
    user_key: str
    recipes: list[CustomMosRecipe] = []
    updated_at: datetime


class CustomMosRecipeCreateRequest(BaseModel):
    mos_code: str = Field(min_length=2, max_length=10)
    title: str = Field(min_length=2, max_length=120)
    parent_agent: str
    focus_areas: list[str] = Field(min_length=1, max_length=8)
    starter_prompt: str = Field(default="", max_length=500)


class CustomMosRecipeListResponse(BaseModel):
    recipes: list[CustomMosRecipe]
    message: str
