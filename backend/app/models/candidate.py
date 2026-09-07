from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    resume_text: Mapped[str] = mapped_column(Text)
    resume_info: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
