from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment
from app.models.test_case import TestCase


async def get_progress(experiment_id: int, redis: Redis) -> dict[int, int]:
    """Return {variant_id: completed_count} for all variants of an experiment."""
    pattern = f"progress:{experiment_id}:*"
    keys: list[str] = await redis.keys(pattern)
    result: dict[int, int] = {}
    for key in keys:
        parts = key.split(":")
        if len(parts) == 3:
            variant_id = int(parts[2])
            raw = await redis.get(key)
            result[variant_id] = int(raw) if raw else 0
    return result


async def total_cases(experiment_id: int, db: AsyncSession) -> int:
    """Return the number of test cases in the dataset bound to this experiment."""
    row = await db.execute(
        select(func.count(TestCase.id))
        .join(Experiment, TestCase.dataset_id == Experiment.dataset_id)
        .where(Experiment.id == experiment_id)
    )
    return row.scalar_one()
