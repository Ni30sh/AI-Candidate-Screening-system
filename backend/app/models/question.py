from uuid import uuid4
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[str] = mapped_column(String(20))
    question_type: Mapped[str] = mapped_column(String(30))
    retrieved_context: Mapped[list] = mapped_column(JSON, default=list)
    generation_trace: Mapped[dict] = mapped_column(JSON, default=dict)
    session: Mapped["InterviewSession"] = relationship(back_populates="questions")
    answer: Mapped["Answer | None"] = relationship(back_populates="question", cascade="all, delete-orphan", uselist=False)
