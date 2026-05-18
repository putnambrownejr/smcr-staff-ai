from pydantic import BaseModel, Field

from app.schemas.ingestion import MessageRecord


class MessageWatchRefreshResponse(BaseModel):
    records: list[MessageRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
