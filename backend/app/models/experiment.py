from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExperimentStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"), nullable=False, index=True
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, native_enum=False), nullable=False, default=ExperimentStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    dataset: Mapped[Dataset] = relationship()
    variants: Mapped[list[Variant]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )
    experiment_dimensions: Mapped[list[ExperimentDimension]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentDimension(Base):
    __tablename__ = "experiment_dimensions"

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), primary_key=True
    )
    dimension_id: Mapped[int] = mapped_column(
        ForeignKey("dimensions.id", ondelete="CASCADE"), primary_key=True
    )

    experiment: Mapped[Experiment] = relationship(back_populates="experiment_dimensions")
    dimension: Mapped[Dimension] = relationship(back_populates="experiment_dimensions")
