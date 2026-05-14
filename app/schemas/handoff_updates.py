from pydantic import BaseModel, ConfigDict, Field

from app.schemas.session import CareerTrend, FitrepReminder, HandoffUpsertResponse, PmeStatus, UserSessionHandoff


class HandoffUpdateDraftRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "notes": (
                    "- PME: EWSDEP incomplete due 2026-06-30\n"
                    "- FitRep Annual for MRO due 06/15/2026\n"
                    "- DTS voucher after drill\n"
                    "- Every drill confirm uniform and haircut"
                )
            }
        }
    )
    notes: str = Field(min_length=1, max_length=50000)
    title: str | None = None


class HandoffUpdatePatch(BaseModel):
    pme: list[PmeStatus] = Field(default_factory=list)
    fitreps: list[FitrepReminder] = Field(default_factory=list)
    recurring_drill_notes: list[str] = Field(default_factory=list)
    admin_watch_items: list[str] = Field(default_factory=list)
    career_trends: list[CareerTrend] = Field(default_factory=list)
    recommended_books: list[str] = Field(default_factory=list)
    recommended_courses: list[str] = Field(default_factory=list)
    preferences: dict[str, str] = Field(default_factory=dict)


class HandoffDraftUpdateResponse(BaseModel):
    user_key: str
    title: str
    existing_handoff: UserSessionHandoff | None = None
    proposed_handoff: UserSessionHandoff
    patch: HandoffUpdatePatch
    warnings: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    confirmation_required: bool = True


class HandoffApplyUpdateRequest(BaseModel):
    patch: HandoffUpdatePatch


class HandoffApplyUpdateResponse(HandoffUpsertResponse):
    applied_categories: list[str] = Field(default_factory=list)
