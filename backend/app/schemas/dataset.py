from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    created_at: datetime


class TestCaseCreate(BaseModel):
    input: str
    reference_output: str
    metadata: Optional[dict] = None


class TestCaseBulkCreate(BaseModel):
    cases: list[TestCaseCreate]


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    input: str
    reference_output: str
    metadata: Optional[dict] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def _remap_metadata(cls, data: Any) -> Any:
        # ORM object uses metadata_ due to SQLAlchemy reserved name conflict
        if hasattr(data, "metadata_"):
            return {
                "id": data.id,
                "dataset_id": data.dataset_id,
                "input": data.input,
                "reference_output": data.reference_output,
                "metadata": data.metadata_,
            }
        return data
