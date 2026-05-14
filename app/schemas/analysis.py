from pydantic import BaseModel, ConfigDict, Field


class TextAnalysisRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "focus": "drill weekend prep",
                "text": (
                    "Planning notes for drill. Confirm muster timeline with the company office. "
                    "DTS voucher due NLT 06/10/2026. Prepare uniform and pack field gear."
                ),
            }
        }
    )
    text: str = Field(min_length=1, max_length=50000)
    title: str | None = None
    focus: str | None = None
    max_summary_points: int = Field(default=4, ge=1, le=10)
    max_action_items: int = Field(default=6, ge=1, le=15)
    max_follow_up_questions: int = Field(default=4, ge=1, le=10)
    include_checklist: bool = True
    include_due_outs: bool = True


class TextAnalysisResponse(BaseModel):
    title: str
    summary_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    due_outs: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    stored: bool = False
    storage_note: str = "Request text was analyzed locally and not stored."
