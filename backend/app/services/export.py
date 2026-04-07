from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.result import EvalResult
from app.models.test_case import TestCase
from app.models.variant import Variant


async def golden_jsonl_rows(
    experiment_id: int, db: AsyncSession
) -> AsyncGenerator[str, None]:
    """Yield JSONL lines for golden samples in OpenAI chat format."""
    rows = await db.execute(
        select(EvalResult, TestCase)
        .join(Variant, EvalResult.variant_id == Variant.id)
        .join(TestCase, EvalResult.test_case_id == TestCase.id)
        .where(Variant.experiment_id == experiment_id)
        .where(EvalResult.is_golden.is_(True))
    )
    for eval_result, test_case in rows.all():
        record = {
            "messages": [
                {"role": "user", "content": test_case.input},
                {"role": "assistant", "content": eval_result.raw_output},
            ]
        }
        yield json.dumps(record) + "\n"
