import pytest

from app.services.eval.aggregate import DimensionScore, weighted_aggregate
from app.services.eval.exact import exact_match, normalized_match
from app.services.eval.rouge import rouge_l_score


class TestExactMatch:
    def test_identical_strings(self):
        assert exact_match("hello world", "hello world") is True

    def test_different_strings(self):
        assert exact_match("hello", "world") is False

    def test_case_sensitive(self):
        assert exact_match("Hello", "hello") is False

    def test_empty_strings(self):
        assert exact_match("", "") is True


class TestNormalizedMatch:
    def test_case_insensitive(self):
        assert normalized_match("Hello World", "hello world") is True

    def test_strips_punctuation(self):
        assert normalized_match("hello, world!", "hello world") is True

    def test_different_content(self):
        assert normalized_match("foo", "bar") is False

    def test_normalizes_whitespace(self):
        assert normalized_match("hello  world", "hello world") is True


class TestRougeL:
    def test_identical_strings(self):
        score = rouge_l_score("the cat sat on the mat", "the cat sat on the mat")
        assert score == pytest.approx(1.0)

    def test_empty_prediction(self):
        score = rouge_l_score("", "reference text")
        assert score == pytest.approx(0.0)

    def test_partial_overlap(self):
        score = rouge_l_score("the cat sat", "the cat sat on the mat")
        assert 0.0 < score < 1.0

    def test_no_overlap(self):
        score = rouge_l_score("xyz abc", "hello world test")
        assert score == pytest.approx(0.0)


class TestWeightedAggregate:
    def test_single_dimension(self):
        scores = [DimensionScore(dimension_id=1, score=0.8)]
        weights = {1: 0.5}
        assert weighted_aggregate(scores, weights) == pytest.approx(0.8)

    def test_equal_weights(self):
        scores = [
            DimensionScore(dimension_id=1, score=0.6),
            DimensionScore(dimension_id=2, score=0.4),
        ]
        weights = {1: 0.5, 2: 0.5}
        assert weighted_aggregate(scores, weights) == pytest.approx(0.5)

    def test_unequal_weights_not_summing_to_one(self):
        scores = [
            DimensionScore(dimension_id=1, score=1.0),
            DimensionScore(dimension_id=2, score=0.0),
        ]
        weights = {1: 3.0, 2: 1.0}
        # weighted sum = 3.0; total weight = 4.0 → 0.75
        assert weighted_aggregate(scores, weights) == pytest.approx(0.75)

    def test_empty_scores(self):
        assert weighted_aggregate([], {1: 1.0}) == pytest.approx(0.0)

    def test_zero_total_weight(self):
        scores = [DimensionScore(dimension_id=1, score=0.9)]
        assert weighted_aggregate(scores, {}) == pytest.approx(0.0)
