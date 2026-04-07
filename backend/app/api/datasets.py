from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.models.dataset import Dataset
from app.models.test_case import TestCase
from app.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    TestCaseBulkCreate,
    TestCaseResponse,
)

router = APIRouter()


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    body: DatasetCreate, db: AsyncSession = Depends(get_db)
) -> DatasetResponse:
    dataset = Dataset(name=body.name, description=body.description)
    db.add(dataset)
    try:
        await db.commit()
        await db.refresh(dataset)
    except IntegrityError:
        await db.rollback()
        raise ConflictError(f"Dataset with name '{body.name}' already exists")
    return DatasetResponse.model_validate(dataset)


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(db: AsyncSession = Depends(get_db)) -> list[DatasetResponse]:
    rows = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    return [DatasetResponse.model_validate(d) for d in rows.scalars().all()]


@router.post("/{dataset_id}/cases", response_model=list[TestCaseResponse], status_code=201)
async def bulk_upload_cases(
    dataset_id: int,
    body: TestCaseBulkCreate,
    db: AsyncSession = Depends(get_db),
) -> list[TestCaseResponse]:
    row = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    if row.scalar_one_or_none() is None:
        raise NotFoundError("Dataset", dataset_id)

    cases = [
        TestCase(
            dataset_id=dataset_id,
            input=c.input,
            reference_output=c.reference_output,
            metadata_=c.metadata,
        )
        for c in body.cases
    ]
    db.add_all(cases)
    await db.commit()
    for case in cases:
        await db.refresh(case)
    return [TestCaseResponse.model_validate(c) for c in cases]


@router.get("/{dataset_id}/cases", response_model=list[TestCaseResponse])
async def list_cases(
    dataset_id: int, db: AsyncSession = Depends(get_db)
) -> list[TestCaseResponse]:
    row = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    if row.scalar_one_or_none() is None:
        raise NotFoundError("Dataset", dataset_id)

    rows = await db.execute(
        select(TestCase).where(TestCase.dataset_id == dataset_id).order_by(TestCase.id)
    )
    return [TestCaseResponse.model_validate(c) for c in rows.scalars().all()]
