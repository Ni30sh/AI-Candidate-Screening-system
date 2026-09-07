from datetime import datetime, timezone
import hashlib
import secrets
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.answer import Answer
from app.models.candidate import Candidate
from app.models.interview import InterviewSession
from app.models.question import Question
from app.models.report import Report
from app.services.context_builder import build_context
from app.services.evaluation_service import build_report, evaluate_answer
from app.services.question_generator import generate_question
from app.services.retriever import LocalRetriever
from app.services.roles import get_role


def create_session(db: Session, candidate_id: str, role_id: str) -> tuple[InterviewSession, str]:
    role = get_role(role_id)
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise LookupError("Candidate not found")
    access_token = secrets.token_urlsafe(32)
    session = InterviewSession(candidate_id=candidate.id, role=role.id, access_token_hash=hashlib.sha256(access_token.encode()).hexdigest())
    db.add(session)
    db.flush()
    _create_question(db, session, candidate, 1)
    db.commit()
    db.refresh(session)
    return session, access_token


def token_matches(session: InterviewSession, access_token: str) -> bool:
    return bool(access_token) and secrets.compare_digest(session.access_token_hash, hashlib.sha256(access_token.encode()).hexdigest())


def _create_question(db: Session, session: InterviewSession, candidate: Candidate, number: int) -> Question:
    role = get_role(session.role)
    context = build_context(candidate.resume_info, role, number)
    retrieved = LocalRetriever(get_settings().vector_db_path).search(context["query"], session.role, limit=3)
    question_data = generate_question(role.name, candidate.resume_info, context, retrieved, number)
    question = Question(session_id=session.id, question=question_data["question"], topic=question_data["topic"], difficulty=question_data["difficulty"], question_type=question_data["question_type"], retrieved_context=retrieved, generation_trace={"query": context["query"], "role": role.id, "resume_topics": context["topics"], "source_chunks": question_data["source_chunks"]})
    db.add(question)
    return question


def submit_answer(db: Session, session: InterviewSession, question_id: str, answer_text: str, duration_seconds: float | None = None) -> InterviewSession:
    question = db.get(Question, question_id)
    if not question or question.session_id != session.id:
        raise LookupError("Question not found in this session")
    if question.answer:
        raise ValueError("This question has already been answered")
    evaluation = evaluate_answer(answer_text, {"topic": question.topic, "question": question.question}, session.role, question.retrieved_context)
    answer = Answer(question_id=question.id, answer=answer_text.strip(), transcript=answer_text.strip(), duration_seconds=duration_seconds, evaluation=evaluation, score=evaluation["score"])
    question.answer = answer
    db.add(answer)
    db.flush()
    answered = len([item for item in session.questions if item.answer])
    if answered >= get_settings().questions_per_interview:
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        summary, analysis = build_report(session.questions)
        db.add(Report(session_id=session.id, summary=summary, analysis=analysis))
    else:
        _create_question(db, session, session.candidate, answered + 1)
    db.commit()
    db.refresh(session)
    return session
