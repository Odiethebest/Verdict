from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EvalResult(Base):
    __tablename__ = "eval_results"
    __table_args__ = (
        UniqueConstraint(
            "variant_id", "test_case_id", name="uq_result_variant_test_case"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_output: Mapped[str] = mapped_column(Text, nullable=False)
    rouge_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    judge_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    judge_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exact_match: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    human_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_golden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    variant: Mapped[Variant] = relationship(back_populates="eval_results")
    test_case: Mapped[TestCase] = relationship(back_populates="eval_results")
    dimension_scores: Mapped[list[DimensionScore]] = relationship(
        back_populates="result", cascade="all, delete-orphan"
    )


class DimensionScore(Base):
    __tablename__ = "dimension_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("eval_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dimension_id: Mapped[int] = mapped_column(
        ForeignKey("dimensions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    result: Mapped[EvalResult] = relationship(back_populates="dimension_scores")
    dimension: Mapped[Dimension] = relationship(back_populates="dimension_scores")
