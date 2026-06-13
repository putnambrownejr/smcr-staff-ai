from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FormatPreference(StrEnum):
    naval_letter = "naval_letter"
    bullet = "bullet"
    smeac = "smeac"


class UserProfile(BaseModel):
    user_key: str
    billet: str = ""
    unit: str = ""
    mos: str = ""
    format_preference: FormatPreference = FormatPreference.naval_letter
    one_number_one_rule: bool = True
    style_notes: str = ""
    updated_at: datetime


class UserProfileUpsertRequest(BaseModel):
    billet: str = ""
    unit: str = ""
    mos: str = Field("", max_length=6)
    format_preference: FormatPreference = FormatPreference.naval_letter
    one_number_one_rule: bool = True
    style_notes: str = Field("", max_length=2000)


class UserProfileResponse(BaseModel):
    profile: UserProfile
    message: str
