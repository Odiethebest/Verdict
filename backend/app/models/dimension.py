from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dimension(Base):
    __tablename__ = "dimensions"
    __table_args__ = (
        CheckConstraint("weight > 0", name="ck_dimension_weight_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    scorer_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiment_dimensions: Mapped[list["ExperimentDimension"]] = relationship(
        back_populates="dimension"
    )
    dimension_scores: Mapped[list["DimensionScore"]] = relationship(
        back_populates="dimension"
    )
