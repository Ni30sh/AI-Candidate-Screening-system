from uuid import uuid4
from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), unique=True)
    answer: Mapped[str] = mapped_column(Text)
    transcript: Mapped[str] = mapped_column(Text, default="")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    evaluation: Mapped[dict] = mapped_column(JSON, default=dict)
    score: Mapped[float] = mapped_column(default=0)
    question: Mapped["Question"] = relationship(back_populates="answer")
