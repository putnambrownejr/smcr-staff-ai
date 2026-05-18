from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.calendar import DrillPrepPlanResponse
from app.schemas.ingestion import MessageRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.session import UserSessionHandoff
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.schemas.travel_cases import TravelCaseRecord
from app.schemas.user_context import ActiveUserContext


class ChiefBriefRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_key": "capt-example",
                "maradmin_records": [
                    {
                        "source_id": "maradmin-123-26",
                        "title": "MARADMIN 123/26 Revision of MCO 1610.7 Performance Evaluation System",
                        "canonical_url": "https://example.test/maradmin-123-26",
                        "summary": "This message announces an update to FitRep/PES policy published on MCPEL.",
                    }
                ],
            }
        }
    )
    user_key: str | None = None
    include_personal_documents: bool = True
    include_drill_plans: bool = True
    maradmin_records: list[MessageRecord] = Field(default_factory=list)


class ChiefActionItem(BaseModel):
    title: str
    category: str
    priority: str = "medium"
    due_date: date | None = None
    source: str | None = None
    recommendation: str


class NextDrillReadiness(BaseModel):
    anchor_drill_date: date | None = None
    readiness_posture: str
    summary: list[str] = Field(default_factory=list)
    decisive_action: str | None = None
    this_week_focus: list[str] = Field(default_factory=list)
    must_do_before_drill: list[ChiefActionItem] = Field(default_factory=list)
    ready_if: list[str] = Field(default_factory=list)
    likely_friction_points: list[str] = Field(default_factory=list)
    missing_foundation: list[str] = Field(default_factory=list)
    standing_rhythm: list[str] = Field(default_factory=list)
    recommended_follow_on_workflows: list[str] = Field(default_factory=list)


class ThinStaffAssist(BaseModel):
    posture: str
    summary: list[str] = Field(default_factory=list)
    likely_blind_spots: list[str] = Field(default_factory=list)
    missing_section_questions: list[str] = Field(default_factory=list)
    recommended_products: list[str] = Field(default_factory=list)
    walk_in_brief: list[str] = Field(default_factory=list)
    changes_since_last_time: list[str] = Field(default_factory=list)
    next_touchpoint: str | None = None


class ChiefBriefResponse(BaseModel):
    title: str
    user_key: str | None = None
    handoff: UserSessionHandoff | None = None
    active_user_context: ActiveUserContext | None = None
    handoff_is_stale: bool = False
    next_drill_readiness: NextDrillReadiness
    thin_staff_assist: ThinStaffAssist
    summary_lines: list[str] = Field(default_factory=list)
    action_items: list[ChiefActionItem]
    top_priority_items: list[ChiefActionItem] = Field(default_factory=list)
    document_summary: PersonalDocumentSummary | None = None
    drill_plans: list[DrillPrepPlanResponse] = Field(default_factory=list)
    travel_cases: list[TravelCaseRecord] = Field(default_factory=list)
    documentation_updates: list[DocumentationUpdateCandidate] = Field(default_factory=list)
    reading_recommendations: list[str] = Field(default_factory=list)
    recommended_courses: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
