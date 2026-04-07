import re
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import ScoringError

_JUDGE_TEMPLATE = """\
You are an impartial evaluation judge. Score the LLM output below based on the specified dimension.

## Dimension
Name: {dimension_name}
Scoring criteria: {scorer_prompt}

## Task
Input: {input}
Reference output: {reference}
Actual output: {output}

## Instructions
Respond with exactly two lines:
Score: <number between 0.0 and 1.0>
Reasoning: <one sentence explaining the score>
"""


@dataclass
class DimensionConfig:
    id: int
    name: str
    scorer_prompt: str
    weight: float


@dataclass
class JudgeResult:
    score: float
    reasoning: str


def _parse_judge_response(content: str) -> JudgeResult:
    score_match = re.search(r"Score:\s*([0-9]*\.?[0-9]+)", content, re.IGNORECASE)
    reasoning_match = re.search(
        r"Reasoning:\s*(.+)", content, re.IGNORECASE | re.DOTALL
    )

    if not score_match:
        raise ScoringError(
            f"Could not parse numeric score from judge response: {content!r}"
        )

    score = float(score_match.group(1))
    if not (0.0 <= score <= 1.0):
        raise ScoringError(f"Judge score {score} is outside [0.0, 1.0]")

    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
    return JudgeResult(score=score, reasoning=reasoning)


async def judge_score(
    input: str,
    output: str,
    reference: str,
    dimension: DimensionConfig,
    client: AsyncOpenAI,
) -> JudgeResult:
    """Call the LLM judge and return a parsed JudgeResult.

    Raises ScoringError if the response cannot be parsed.
    """
    prompt = _JUDGE_TEMPLATE.format(
        dimension_name=dimension.name,
        scorer_prompt=dimension.scorer_prompt,
        input=input,
        reference=reference,
        output=output,
    )

    response = await client.chat.completions.create(
        model=settings.JUDGE_MODEL,
        temperature=settings.JUDGE_TEMPERATURE,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content or ""
    return _parse_judge_response(content)
