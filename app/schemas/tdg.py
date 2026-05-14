from pydantic import BaseModel, ConfigDict, Field


class TdgGenerationRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Reserve convoy link-up",
                "theme": "small-unit decision-making under time pressure",
                "audience": "company-grade officers and SNCOs",
                "training_objective": "Practice tactical judgment and risk tradeoffs.",
                "references": ["MCDP 1 Warfighting", "MCDP 3 Tactics"],
                "constraints": ["Reserve training audience", "45-minute session"],
            }
        }
    )

    title: str
    theme: str
    audience: str | None = None
    training_objective: str
    references: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    include_sketch_map_prompt: bool = True


class TdgGenerationResponse(BaseModel):
    title: str
    context: list[str] = Field(default_factory=list)
    mettc_prompts: list[str] = Field(default_factory=list)
    decision_points: list[str] = Field(default_factory=list)
    discussion_questions: list[str] = Field(default_factory=list)
    instructor_notes: list[str] = Field(default_factory=list)
    sketch_map_prompt: str | None = None
    warnings: list[str] = Field(default_factory=list)
