from pydantic import BaseModel, ConfigDict, Field


class PoamRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Drill support order POA&M",
                "higher_guidance": [
                    "Establish reporting timeline for drill weekend support.",
                    "Coordinate S-6 comm checks and S-4 logistics support.",
                ],
                "warfighting_functions": ["command and control", "logistics", "fires", "intelligence"],
                "staff_sections": ["S-1", "S-3", "S-4", "S-6"],
            }
        }
    )

    title: str
    higher_guidance: list[str] = Field(default_factory=list)
    warfighting_functions: list[str] = Field(default_factory=list)
    staff_sections: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class PoamLineItem(BaseModel):
    workstream: str
    owner: str
    task: str
    suspense_hint: str
    coordination: list[str] = Field(default_factory=list)


class PoamResponse(BaseModel):
    title: str
    summary_lines: list[str] = Field(default_factory=list)
    line_items: list[PoamLineItem] = Field(default_factory=list)
    review_points: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
