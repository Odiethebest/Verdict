from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeedbackUpdate(BaseModel):
    human_score: float
    is_golden: bool = True


class DimensionScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dimension_id: int
    score: float
    reasoning: str | None


class EvalResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_id: int
    test_case_id: int
    raw_output: str
    rouge_score: float | None
    judge_score: float | None
    judge_reasoning: str | None
    exact_match: bool | None
    human_score: float | None
    is_golden: bool
    created_at: datetime
    dimension_scores: list[DimensionScoreResponse]
