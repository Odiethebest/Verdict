from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    reference_output: Mapped[str] = mapped_column(Text, nullable=False)
    # 'metadata' is reserved by DeclarativeBase; use 'metadata_' with explicit column name
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="test_cases")
    eval_results: Mapped[list["EvalResult"]] = relationship(back_populates="test_case")
