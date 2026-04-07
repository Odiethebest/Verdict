import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment, ExperimentStatus
from app.models.result import EvalResult
from app.models.variant import Variant


@pytest.mark.asyncio
async def test_submit_feedback_sets_human_score(
    client: AsyncClient, db_session: AsyncSession
):
    # Seed minimal records directly into the test DB session
    from app.models.dataset import Dataset
    from app.models.test_case import TestCase

    dataset = Dataset(name="FeedbackDS")
    db_session.add(dataset)
    await db_session.flush()

    test_case = TestCase(dataset_id=dataset.id, input="Q", reference_output="A")
    db_session.add(test_case)
    await db_session.flush()

    experiment = Experiment(
        name="FeedbackExp", dataset_id=dataset.id, status=ExperimentStatus.completed
    )
    db_session.add(experiment)
    await db_session.flush()

    variant = Variant(
        experiment_id=experiment.id,
        name="v1",
        model="gpt-4o-mini",
        system_prompt="You are helpful.",
        temperature=0.0,
    )
    db_session.add(variant)
    await db_session.flush()

    eval_result = EvalResult(
        variant_id=variant.id,
        test_case_id=test_case.id,
        raw_output="Answer",
        is_golden=False,
    )
    db_session.add(eval_result)
    await db_session.commit()
    await db_session.refresh(eval_result)

    response = await client.patch(
        f"/api/results/{eval_result.id}/feedback",
        json={"human_score": 0.9, "is_golden": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["human_score"] == pytest.approx(0.9)
    assert data["is_golden"] is True


@pytest.mark.asyncio
async def test_submit_feedback_not_found(client: AsyncClient):
    response = await client.patch(
        "/api/results/9999/feedback",
        json={"human_score": 0.5, "is_golden": False},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_feedback_preserves_human_score_on_update(
    client: AsyncClient, db_session: AsyncSession
):
    from app.models.dataset import Dataset
    from app.models.test_case import TestCase

    dataset = Dataset(name="FeedbackDS2")
    db_session.add(dataset)
    await db_session.flush()

    test_case = TestCase(dataset_id=dataset.id, input="Q2", reference_output="A2")
    db_session.add(test_case)
    await db_session.flush()

    experiment = Experiment(
        name="FeedbackExp2", dataset_id=dataset.id, status=ExperimentStatus.completed
    )
    db_session.add(experiment)
    await db_session.flush()

    variant = Variant(
        experiment_id=experiment.id,
        name="v1",
        model="gpt-4o-mini",
        system_prompt="sys",
        temperature=0.0,
    )
    db_session.add(variant)
    await db_session.flush()

    eval_result = EvalResult(
        variant_id=variant.id,
        test_case_id=test_case.id,
        raw_output="Out",
        is_golden=False,
        human_score=0.7,
    )
    db_session.add(eval_result)
    await db_session.commit()
    await db_session.refresh(eval_result)

    # Override with a new score
    response = await client.patch(
        f"/api/results/{eval_result.id}/feedback",
        json={"human_score": 0.4, "is_golden": False},
    )
    assert response.status_code == 200
    assert response.json()["human_score"] == pytest.approx(0.4)
    assert response.json()["is_golden"] is False
