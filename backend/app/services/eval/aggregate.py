from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DimensionScore:
    dimension_id: int
    score: float


def weighted_aggregate(
    dimension_scores: list[DimensionScore],
    weights: dict[int, float],
) -> float:
    """Return the weighted average score, normalized by the sum of applicable weights.

    Uses only weights for dimensions present in dimension_scores.
    Handles cases where weights do not sum to 1.0.
    """
    if not dimension_scores:
        return 0.0

    total_weight = sum(weights.get(ds.dimension_id, 0.0) for ds in dimension_scores)
    if total_weight == 0.0:
        return 0.0

    weighted_sum = sum(
        ds.score * weights.get(ds.dimension_id, 0.0) for ds in dimension_scores
    )
    return weighted_sum / total_weight
