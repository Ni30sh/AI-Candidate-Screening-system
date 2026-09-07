from pathlib import Path
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.interview import InterviewSession
from app.schemas.api import AnswerCreate, ReportResponse, ResumeResponse, Role, SessionCreate, SessionResponse
from app.services.interview_service import create_session, submit_answer, token_matches
from app.services.resume_analyzer import analyze_resume
from app.services.resume_parser import extract_resume
from app.services.roles import ROLES, get_role

router = APIRouter()


def question_view(question):
    return {"id": question.id, "question": question.question, "topic": question.topic, "difficulty": question.difficulty, "question_type": question.question_type}


def session_view(session: InterviewSession) -> dict:
    current = next((question for question in session.questions if question.answer is None), None)
    return {"session_id": session.id, "role": session.role, "status": session.status, "total_questions": get_settings().questions_per_interview, "answered_questions": len([q for q in session.questions if q.answer]), "current_question": question_view(current) if current else None}


def authorized_session(session_id: str, access_token: str, db: Session) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Interview session not found")
    if not token_matches(session, access_token):
        raise HTTPException(401, "Valid session token required")
    return session

@router.get("/roles", response_model=list[Role])
def roles():
    return list(ROLES.values())

@router.post("/resumes", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = get_settings()
    filename = Path(file.filename or "resume.txt").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        raise HTTPException(415, "Only PDF and text resumes are supported")
    content = await file.read()
    if len(content) > settings.upload_max_bytes:
        raise HTTPException(413, "Resume file is too large")
    if suffix == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(422, "The uploaded file is not a valid PDF")
    if suffix == ".txt" and b"\x00" in content:
        raise HTTPException(422, "The text resume contains invalid binary data")
    try:
        text = extract_resume(filename, content)
        info = analyze_resume(text)
        candidate = Candidate(resume_text=text, resume_info=info)
        db.add(candidate)
        db.commit()
        return {"candidate_id": candidate.id, "filename": filename, "resume_info": info}
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(422, "Resume processing failed") from exc

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(payload: SessionCreate, db: Session = Depends(get_db)):
    try:
        session, access_token = create_session(db, payload.candidate_id, payload.role)
        return {**session_view(session), "access_token": access_token}
    except (ValueError, LookupError) as exc:
        raise HTTPException(400, str(exc)) from exc

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, x_session_token: str = Header(default=""), db: Session = Depends(get_db)):
    session = authorized_session(session_id, x_session_token, db)
    return session_view(session)

@router.post("/sessions/{session_id}/questions/{question_id}/answers", response_model=SessionResponse)
def answer_question(session_id: str, question_id: str, payload: AnswerCreate, x_session_token: str = Header(default=""), db: Session = Depends(get_db)):
    session = authorized_session(session_id, x_session_token, db)
    if session.status != "active":
        raise HTTPException(409, "Interview is already finished")
    try:
        return session_view(submit_answer(db, session, question_id, payload.answer, payload.duration_seconds))
    except (ValueError, LookupError) as exc:
        raise HTTPException(400, str(exc)) from exc

@router.get("/sessions/{session_id}/results", response_model=ReportResponse)
def get_results(session_id: str, x_session_token: str = Header(default=""), db: Session = Depends(get_db)):
    session = authorized_session(session_id, x_session_token, db)
    if not session.report:
        raise HTTPException(409, "Interview is not complete")
    return {"session_id": session.id, "summary": session.report.summary, "analysis": session.report.analysis, "questions": [{**question_view(q), "answer": q.answer.answer if q.answer else None, "evaluation": q.answer.evaluation if q.answer else None, "retrieved_context": q.retrieved_context} for q in session.questions]}
