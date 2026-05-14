from pydantic import BaseModel, ConfigDict, Field


class DataRecord(BaseModel):
    record_id: str
    fields: dict[str, str] = Field(default_factory=dict)


class DataMergeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "left_records": [
                    {"record_id": "left-1", "fields": {"name": "Capt Example", "mos": "0602", "unit": "6th Comm Bn"}}
                ],
                "right_records": [
                    {
                        "record_id": "right-1",
                        "fields": {"name": "Captain Example", "mos": "0602", "unit": "6th Comm Battalion"},
                    }
                ],
                "compare_fields": ["name", "mos", "unit"],
                "similarity_threshold": 0.7,
            }
        }
    )

    left_records: list[DataRecord] = Field(default_factory=list)
    right_records: list[DataRecord] = Field(default_factory=list)
    compare_fields: list[str] = Field(default_factory=list)
    similarity_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    max_matches: int = Field(default=20, ge=1, le=200)


class DataMatchCandidate(BaseModel):
    left_record_id: str
    right_record_id: str
    similarity: float
    matched_fields: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DataMergeResponse(BaseModel):
    summary_lines: list[str] = Field(default_factory=list)
    merged_rows: list[dict[str, str]] = Field(default_factory=list)
    match_candidates: list[DataMatchCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
