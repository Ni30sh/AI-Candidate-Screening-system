from typing import Any
from pydantic import BaseModel, Field


class Role(BaseModel):
    id: str
    name: str
    description: str


class ResumeResponse(BaseModel):
    candidate_id: str
    filename: str
    resume_info: dict[str, Any]


class SessionCreate(BaseModel):
    candidate_id: str
    role: str


class SessionResponse(BaseModel):
    session_id: str
    role: str
    status: str
    total_questions: int
    answered_questions: int
    current_question: dict[str, Any] | None = None
    access_token: str | None = None


class AnswerCreate(BaseModel):
    answer: str = Field(min_length=1, max_length=10_000)
    duration_seconds: float | None = Field(default=None, ge=0, le=3600)


class ReportResponse(BaseModel):
    session_id: str
    summary: str
    analysis: dict[str, Any]
    questions: list[dict[str, Any]]
