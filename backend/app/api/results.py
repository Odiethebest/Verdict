from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.result import EvalResult
from app.schemas.result import EvalResultResponse, FeedbackUpdate

router = APIRouter()


@router.patch("/{result_id}/feedback", response_model=EvalResultResponse)
async def submit_feedback(
    result_id: int,
    body: FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
) -> EvalResultResponse:
    row = await db.execute(
        select(EvalResult)
        .where(EvalResult.id == result_id)
        .options(selectinload(EvalResult.dimension_scores))
    )
    eval_result = row.scalar_one_or_none()
    if eval_result is None:
        raise NotFoundError("EvalResult", result_id)

    eval_result.human_score = body.human_score
    eval_result.is_golden = body.is_golden

    await db.commit()
    await db.refresh(eval_result)
    return EvalResultResponse.model_validate(eval_result)
