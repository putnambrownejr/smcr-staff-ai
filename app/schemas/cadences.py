from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CadenceRating(StrEnum):
    clean = "clean"
    adult = "adult"


class CadenceCreateRequest(BaseModel):
    user_key: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=8_000)
    use: str = Field(default="unit PT", max_length=80)
    tempo: str = Field(default="moderate", max_length=40)
    rating: CadenceRating = CadenceRating.clean


class CadenceRecord(BaseModel):
    cadence_id: str
    title: str
    text: str
    use: str
    tempo: str
    rating: CadenceRating
    built_in: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CadenceLibraryResponse(BaseModel):
    records: list[CadenceRecord] = Field(default_factory=list)
    adult_content_included: bool = False
    policy: str = (
        "Adult is opt-in and never permits slurs, targeted harassment, hazing, sexual violence, "
        "or targeted degradation."
    )
