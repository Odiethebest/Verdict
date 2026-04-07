import asyncio
import logging
from datetime import datetime, timezone

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import ScoringError
from app.models.dimension import Dimension
from app.models.experiment import Experiment, ExperimentDimension, ExperimentStatus
from app.models.result import DimensionScore as DimensionScoreModel
from app.models.result import EvalResult
from app.models.test_case import TestCase
from app.models.variant import Variant
from app.services.eval.aggregate import DimensionScore as AggDimScore
from app.services.eval.aggregate import weighted_aggregate
from app.services.eval.exact import exact_match
from app.services.eval.judge import DimensionConfig, judge_score
from app.services.eval.rouge import rouge_l_score

logger = logging.getLogger(__name__)


async def _call_llm_with_retry(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    user_input: str,
    temperature: float,
    semaphore: asyncio.Semaphore,
) -> str:
    """Call the OpenAI chat completion API with exponential backoff on 429."""
    max_attempts = 3
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        async with semaphore:
            try:
                response = await client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input},
                    ],
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                if status_code == 429 and attempt < max_attempts - 1:
                    wait = 2**attempt
                    logger.warning("Rate limited; retrying in %ss (attempt %d)", wait, attempt + 1)
                    await asyncio.sleep(wait)
                    last_exc = exc
                    continue
                raise

    raise last_exc  # type: ignore[misc]  # unreachable if max_attempts >= 1


async def _run_variant(
    variant: Variant,
    test_cases: list[TestCase],
    dimensions: list[Dimension],
    semaphore: asyncio.Semaphore,
    redis: Redis,
    experiment_id: int,
) -> None:
    """Process all test cases for one variant using its own DB session."""
    from app.core.database import AsyncSessionLocal  # avoid circular import at module level

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    dim_configs = [
        DimensionConfig(id=d.id, name=d.name, scorer_prompt=d.scorer_prompt, weight=d.weight)
        for d in dimensions
    ]
    weights = {d.id: d.weight for d in dimensions}

    async with AsyncSessionLocal() as db:
        for test_case in test_cases:
            raw_output = await _call_llm_with_retry(
                client=client,
                model=variant.model,
                system_prompt=variant.system_prompt,
                user_input=test_case.input,
                temperature=variant.temperature,
                semaphore=semaphore,
            )

            em = exact_match(raw_output, test_case.reference_output)
            rouge = rouge_l_score(raw_output, test_case.reference_output)

            judge_results: list[tuple[DimensionConfig, float, str]] = []
            for dim_cfg in dim_configs:
                try:
                    result = await judge_score(
                        input=test_case.input,
                        output=raw_output,
                        reference=test_case.reference_output,
                        dimension=dim_cfg,
                        client=client,
                    )
                    judge_results.append((dim_cfg, result.score, result.reasoning))
                except ScoringError:
                    logger.exception(
                        "Judge scoring failed for variant=%d case=%d dim=%d",
                        variant.id,
                        test_case.id,
                        dim_cfg.id,
                    )
                    judge_results.append((dim_cfg, 0.0, ""))

            agg_scores = [AggDimScore(dimension_id=dc.id, score=s) for dc, s, _ in judge_results]
            overall_judge = weighted_aggregate(agg_scores, weights)
            primary_reasoning = judge_results[0][2] if judge_results else None

            eval_result = EvalResult(
                variant_id=variant.id,
                test_case_id=test_case.id,
                raw_output=raw_output,
                rouge_score=rouge,
                judge_score=overall_judge,
                judge_reasoning=primary_reasoning,
                exact_match=em,
                is_golden=False,
            )
            db.add(eval_result)
            await db.flush()

            for dim_cfg, score, reasoning in judge_results:
                db.add(
                    DimensionScoreModel(
                        result_id=eval_result.id,
                        dimension_id=dim_cfg.id,
                        score=score,
                        reasoning=reasoning or None,
                    )
                )

            await db.commit()
            await redis.incr(f"progress:{experiment_id}:{variant.id}")


async def run_experiment(
    experiment_id: int,
    db: AsyncSession,
    redis: Redis,
) -> None:
    """Orchestrate a full experiment run.

    Sets experiment status to running, dispatches all variants concurrently
    (bounded by EVAL_CONCURRENCY semaphore), then marks completed or failed.
    """
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()
    if experiment is None:
        raise ValueError(f"Experiment {experiment_id} not found")

    experiment.status = ExperimentStatus.running
    await db.commit()

    try:
        variants_rows = await db.execute(
            select(Variant).where(Variant.experiment_id == experiment_id)
        )
        variants = list(variants_rows.scalars().all())

        cases_rows = await db.execute(
            select(TestCase).where(TestCase.dataset_id == experiment.dataset_id)
        )
        test_cases = list(cases_rows.scalars().all())

        dim_id_rows = await db.execute(
            select(ExperimentDimension.dimension_id).where(
                ExperimentDimension.experiment_id == experiment_id
            )
        )
        dim_ids = [r[0] for r in dim_id_rows.all()]

        dim_rows = await db.execute(
            select(Dimension).where(Dimension.id.in_(dim_ids))
        )
        dimensions = list(dim_rows.scalars().all())

        semaphore = asyncio.Semaphore(settings.EVAL_CONCURRENCY)

        await asyncio.gather(
            *[
                _run_variant(
                    variant=v,
                    test_cases=test_cases,
                    dimensions=dimensions,
                    semaphore=semaphore,
                    redis=redis,
                    experiment_id=experiment_id,
                )
                for v in variants
            ]
        )

        experiment.status = ExperimentStatus.completed
        experiment.completed_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception:
        logger.exception("Experiment %d failed", experiment_id)
        experiment.status = ExperimentStatus.failed
        experiment.completed_at = datetime.now(timezone.utc)
        await db.commit()
        raise
