from datetime import datetime

from pydantic import BaseModel, Field


class BenchSectionsConfig(BaseModel):
    user_key: str
    sections: list[str]
    updated_at: datetime


class BenchSectionsUpsertRequest(BaseModel):
    sections: list[str] = Field(min_length=1)


class BenchSectionsResponse(BaseModel):
    config: BenchSectionsConfig
    message: str
