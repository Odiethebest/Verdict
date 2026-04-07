from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.models.dimension import Dimension
from app.schemas.dimension import DimensionCreate, DimensionResponse, DimensionUpdate

router = APIRouter()


@router.post("", response_model=DimensionResponse, status_code=201)
async def create_dimension(
    body: DimensionCreate, db: AsyncSession = Depends(get_db)
) -> DimensionResponse:
    dimension = Dimension(
        name=body.name, weight=body.weight, scorer_prompt=body.scorer_prompt
    )
    db.add(dimension)
    try:
        await db.commit()
        await db.refresh(dimension)
    except IntegrityError:
        await db.rollback()
        raise ConflictError(f"Dimension with name '{body.name}' already exists")
    return DimensionResponse.model_validate(dimension)


@router.get("", response_model=list[DimensionResponse])
async def list_dimensions(db: AsyncSession = Depends(get_db)) -> list[DimensionResponse]:
    rows = await db.execute(select(Dimension).order_by(Dimension.created_at.desc()))
    return [DimensionResponse.model_validate(d) for d in rows.scalars().all()]


@router.put("/{dimension_id}", response_model=DimensionResponse)
async def update_dimension(
    dimension_id: int,
    body: DimensionUpdate,
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    row = await db.execute(select(Dimension).where(Dimension.id == dimension_id))
    dimension = row.scalar_one_or_none()
    if dimension is None:
        raise NotFoundError("Dimension", dimension_id)

    if body.name is not None:
        dimension.name = body.name
    if body.weight is not None:
        dimension.weight = body.weight
    if body.scorer_prompt is not None:
        dimension.scorer_prompt = body.scorer_prompt

    try:
        await db.commit()
        await db.refresh(dimension)
    except IntegrityError:
        await db.rollback()
        raise ConflictError(f"Dimension with name '{body.name}' already exists")
    return DimensionResponse.model_validate(dimension)


@router.delete("/{dimension_id}", status_code=204, response_model=None)
async def delete_dimension(
    dimension_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    row = await db.execute(select(Dimension).where(Dimension.id == dimension_id))
    dimension = row.scalar_one_or_none()
    if dimension is None:
        raise NotFoundError("Dimension", dimension_id)

    await db.delete(dimension)
    await db.commit()
