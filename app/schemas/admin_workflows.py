from enum import StrEnum

from pydantic import BaseModel, Field


class AdminWorkflowType(StrEnum):
    dts_voucher = "dts_voucher"
    dts_authorization = "dts_authorization"
    mrows_rebuttal = "mrows_rebuttal"
    ridt = "ridt"
    gtcc = "gtcc"
    orders_review = "orders_review"
    admin_package = "admin_package"
    award_package = "award_package"


class AdminWorkflowRequest(BaseModel):
    workflow_type: AdminWorkflowType
    title: str
    facts: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class AdminWorkflowDraftRequest(BaseModel):
    title: str
    facts: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class AdminWorkflowResponse(BaseModel):
    workflow_type: AdminWorkflowType
    title: str
    checklist: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    review_points: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
