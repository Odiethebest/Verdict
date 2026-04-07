from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FeedbackUpdate(BaseModel):
    human_score: float
    is_golden: bool = True


class DimensionScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dimension_id: int
    score: float
    reasoning: Optional[str]


class EvalResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_id: int
    test_case_id: int
    raw_output: str
    rouge_score: Optional[float]
    judge_score: Optional[float]
    judge_reasoning: Optional[str]
    exact_match: Optional[bool]
    human_score: Optional[float]
    is_golden: bool
    created_at: datetime
    dimension_scores: list[DimensionScoreResponse]
