from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class DimensionCreate(BaseModel):
    name: str
    weight: float
    scorer_prompt: str

    @field_validator("weight")
    @classmethod
    def weight_in_range(cls, v: float) -> float:
        if not (0.0 < v <= 1.0):
            raise ValueError("weight must be in (0.0, 1.0]")
        return v


class DimensionUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    scorer_prompt: Optional[str] = None

    @field_validator("weight")
    @classmethod
    def weight_in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 < v <= 1.0):
            raise ValueError("weight must be in (0.0, 1.0]")
        return v


class DimensionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    weight: float
    scorer_prompt: str
    created_at: datetime
