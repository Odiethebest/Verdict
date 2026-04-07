import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from redis.asyncio import Redis

from app.core.database import AsyncSessionLocal, get_db
from app.core.exceptions import ExperimentStateError, NotFoundError
from app.core.redis import get_redis
from app.models.dimension import Dimension
from app.models.experiment import Experiment, ExperimentDimension, ExperimentStatus
from app.models.result import DimensionScore, EvalResult
from app.models.variant import Variant
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentDetailResponse,
    ExperimentResponse,
    LeaderboardEntry,
    VariantCreate,
    VariantResponse,
)
from app.schemas.result import EvalResultResponse
from app.services.eval.aggregate import DimensionScore as AggDimScore
from app.services.eval.aggregate import weighted_aggregate
from app.services.export import golden_jsonl_rows
from app.services.runner.progress import get_progress, total_cases
from app.services.runner.runner import run_experiment

router = APIRouter()


async def _compute_leaderboard(
    experiment_id: int,
    variants: list[Variant],
    db: AsyncSession,
) -> list[LeaderboardEntry]:
    dim_id_rows = await db.execute(
        select(ExperimentDimension.dimension_id).where(
            ExperimentDimension.experiment_id == experiment_id
        )
    )
    dim_ids = [r[0] for r in dim_id_rows.all()]
    if not dim_ids:
        return []

    dim_rows = await db.execute(select(Dimension).where(Dimension.id.in_(dim_ids)))
    weights = {d.id: d.weight for d in dim_rows.scalars().all()}

    entries: list[LeaderboardEntry] = []
    for variant in variants:
        score_rows = await db.execute(
            select(DimensionScore)
            .join(EvalResult, DimensionScore.result_id == EvalResult.id)
            .where(EvalResult.variant_id == variant.id)
        )
        dim_scores = [
            AggDimScore(dimension_id=ds.dimension_id, score=ds.score)
            for ds in score_rows.scalars().all()
        ]
        agg = weighted_aggregate(dim_scores, weights)
        entries.append(
            LeaderboardEntry(
                variant_id=variant.id,
                variant_name=variant.name,
                aggregate_score=agg,
                rank=0,
            )
        )

    entries.sort(key=lambda e: e.aggregate_score, reverse=True)
    for i, entry in enumerate(entries, 1):
        entry.rank = i
    return entries


@router.post("", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    body: ExperimentCreate, db: AsyncSession = Depends(get_db)
) -> ExperimentResponse:
    experiment = Experiment(
        name=body.name,
        dataset_id=body.dataset_id,
        status=ExperimentStatus.pending,
    )
    db.add(experiment)
    await db.flush()

    for dim_id in body.dimension_ids:
        db.add(
            ExperimentDimension(experiment_id=experiment.id, dimension_id=dim_id)
        )

    await db.commit()
    await db.refresh(experiment)
    return ExperimentResponse.model_validate(experiment)


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments(
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentResponse]:
    rows = await db.execute(select(Experiment).order_by(Experiment.created_at.desc()))
    return [ExperimentResponse.model_validate(e) for e in rows.scalars().all()]


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: int, db: AsyncSession = Depends(get_db)
) -> ExperimentDetailResponse:
    row = await db.execute(
        select(Experiment)
        .where(Experiment.id == experiment_id)
        .options(selectinload(Experiment.variants))
    )
    experiment = row.scalar_one_or_none()
    if experiment is None:
        raise NotFoundError("Experiment", experiment_id)

    leaderboard = await _compute_leaderboard(experiment_id, experiment.variants, db)
    return ExperimentDetailResponse(
        id=experiment.id,
        name=experiment.name,
        dataset_id=experiment.dataset_id,
        status=experiment.status,
        created_at=experiment.created_at,
        completed_at=experiment.completed_at,
        variants=[VariantResponse.model_validate(v) for v in experiment.variants],
        leaderboard=leaderboard,
    )


@router.post("/{experiment_id}/variants", response_model=VariantResponse, status_code=201)
async def add_variant(
    experiment_id: int,
    body: VariantCreate,
    db: AsyncSession = Depends(get_db),
) -> VariantResponse:
    row = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    if row.scalar_one_or_none() is None:
        raise NotFoundError("Experiment", experiment_id)

    variant = Variant(
        experiment_id=experiment_id,
        name=body.name,
        model=body.model,
        system_prompt=body.system_prompt,
        temperature=body.temperature,
    )
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return VariantResponse.model_validate(variant)


async def _bg_run_experiment(experiment_id: int, redis: Redis) -> None:
    """Background task wrapper: creates its own DB session."""
    async with AsyncSessionLocal() as db:
        await run_experiment(experiment_id, db, redis)


@router.post("/{experiment_id}/run", status_code=202)
async def trigger_run(
    experiment_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict[str, object]:
    row = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = row.scalar_one_or_none()
    if experiment is None:
        raise NotFoundError("Experiment", experiment_id)

    if experiment.status != ExperimentStatus.pending:
        raise ExperimentStateError(
            f"Experiment status is '{experiment.status.value}', expected 'pending'"
        )

    background_tasks.add_task(_bg_run_experiment, experiment_id, redis)
    return {"message": "Experiment run started", "experiment_id": experiment_id}


@router.get("/{experiment_id}/stream")
async def stream_progress(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> StreamingResponse:
    async def event_generator() -> object:
        n_total = await total_cases(experiment_id, db)
        while True:
            status_row = await db.execute(
                select(Experiment.status).where(Experiment.id == experiment_id)
            )
            status = status_row.scalar_one_or_none()

            progress = await get_progress(experiment_id, redis)
            for variant_id, completed in progress.items():
                payload = json.dumps(
                    {"variant_id": variant_id, "completed": completed, "total": n_total}
                )
                yield f"data: {payload}\n\n"

            if status in (ExperimentStatus.completed, ExperimentStatus.failed):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{experiment_id}/results", response_model=list[EvalResultResponse])
async def get_results(
    experiment_id: int, db: AsyncSession = Depends(get_db)
) -> list[EvalResultResponse]:
    row = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    if row.scalar_one_or_none() is None:
        raise NotFoundError("Experiment", experiment_id)

    rows = await db.execute(
        select(EvalResult)
        .join(Variant, EvalResult.variant_id == Variant.id)
        .where(Variant.experiment_id == experiment_id)
        .options(selectinload(EvalResult.dimension_scores))
    )
    return [EvalResultResponse.model_validate(r) for r in rows.scalars().all()]


@router.get("/{experiment_id}/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    experiment_id: int, db: AsyncSession = Depends(get_db)
) -> list[LeaderboardEntry]:
    row = await db.execute(
        select(Experiment)
        .where(Experiment.id == experiment_id)
        .options(selectinload(Experiment.variants))
    )
    experiment = row.scalar_one_or_none()
    if experiment is None:
        raise NotFoundError("Experiment", experiment_id)

    return await _compute_leaderboard(experiment_id, experiment.variants, db)


@router.get("/{experiment_id}/export")
async def export_golden(
    experiment_id: int, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    row = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    if row.scalar_one_or_none() is None:
        raise NotFoundError("Experiment", experiment_id)

    return StreamingResponse(
        golden_jsonl_rows(experiment_id, db),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f'attachment; filename="golden_{experiment_id}.jsonl"'
        },
    )
