from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ExperimentCreate(BaseModel):
    name: str
    dataset_id: int
    dimension_ids: list[int]


class VariantCreate(BaseModel):
    name: str
    model: str
    system_prompt: str
    temperature: float = 0.0

    @field_validator("temperature")
    @classmethod
    def temperature_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 2.0):
            raise ValueError("temperature must be in [0.0, 2.0]")
        return v


class VariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: int
    name: str
    model: str
    system_prompt: str
    temperature: float


class LeaderboardEntry(BaseModel):
    variant_id: int
    variant_name: str
    aggregate_score: float
    rank: int


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    dataset_id: int
    status: str
    created_at: datetime
    completed_at: datetime | None


class ExperimentDetailResponse(BaseModel):
    id: int
    name: str
    dataset_id: int
    status: str
    created_at: datetime
    completed_at: datetime | None
    variants: list[VariantResponse]
    leaderboard: list[LeaderboardEntry]
