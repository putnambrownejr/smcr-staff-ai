from datetime import datetime

from pydantic import BaseModel


class BenchSectionsConfig(BaseModel):
    user_key: str
    sections: list[str]
    updated_at: datetime


class BenchSectionsUpsertRequest(BaseModel):
    sections: list[str]


class BenchSectionsResponse(BaseModel):
    config: BenchSectionsConfig
    message: str
