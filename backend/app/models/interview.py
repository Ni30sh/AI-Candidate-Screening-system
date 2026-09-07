from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(100), index=True)
    access_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    candidate: Mapped["Candidate"] = relationship(back_populates="sessions")
    questions: Mapped[list["Question"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    report: Mapped["Report | None"] = relationship(back_populates="session", cascade="all, delete-orphan", uselist=False)

Index("ix_session_candidate_status", InterviewSession.candidate_id, InterviewSession.status)
