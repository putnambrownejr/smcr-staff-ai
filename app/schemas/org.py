from pydantic import BaseModel, Field


class OrgUnit(BaseModel):
    unit_id: str
    name: str
    unit_type: str
    component: str
    location: str | None = None
    higher_headquarters_id: str | None = None
    supported_relationships: list[str] = Field(default_factory=list)
    example_data: bool = True


class OrgChainResponse(BaseModel):
    unit_id: str
    chain: list[OrgUnit]
