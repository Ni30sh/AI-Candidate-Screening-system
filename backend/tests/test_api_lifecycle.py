import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app
from app.models import Answer, Candidate, InterviewSession, Question, Report
from app.core.config import get_settings


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(get_settings(), "vector_db_path", str(tmp_path / "missing-index.pkl"))
    monkeypatch.setattr(get_settings(), "questions_per_interview", 5)
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_full_interview_lifecycle(client):
    resume = b"Python FastAPI PostgreSQL project. Experience with machine learning and REST APIs."
    uploaded = client.post("/api/resumes", files={"file": ("resume.txt", resume, "text/plain")})
    assert uploaded.status_code == 201
    candidate_id = uploaded.json()["candidate_id"]

    started = client.post("/api/sessions", json={"candidate_id": candidate_id, "role": "ai-ml-engineer"})
    assert started.status_code == 201
    state = started.json()
    token = state["access_token"]
    assert state["answered_questions"] == 0
    assert state["total_questions"] == 5

    for index in range(5):
        question_id = state["current_question"]["id"]
        response = client.post(f"/api/sessions/{state['session_id']}/questions/{question_id}/answers", headers={"X-Session-Token": token}, json={"answer": f"A detailed technical answer number {index} with trade-offs and validation."})
        assert response.status_code == 200
        state = response.json()
        if index < 4:
            assert state["status"] == "active"
            assert state["answered_questions"] == index + 1
            assert state["current_question"] is not None

    assert state["status"] == "completed"
    assert state["answered_questions"] == 5
    results = client.get(f"/api/sessions/{state['session_id']}/results", headers={"X-Session-Token": token})
    assert results.status_code == 200
    assert len(results.json()["questions"]) == 5
    assert all(item["answer"] for item in results.json()["questions"])

    rejected = client.post(f"/api/sessions/{state['session_id']}/questions/{question_id}/answers", headers={"X-Session-Token": token}, json={"answer": "duplicate"})
    assert rejected.status_code == 409


def test_upload_rejects_unsupported_file(client):
    response = client.post("/api/resumes", files={"file": ("resume.docx", b"content", "application/octet-stream")})
    assert response.status_code == 415


def test_upload_rejects_invalid_pdf_signature(client):
    response = client.post("/api/resumes", files={"file": ("resume.pdf", b"not a pdf", "application/pdf")})
    assert response.status_code == 422


def test_session_rejects_unknown_role(client):
    response = client.post("/api/sessions", json={"candidate_id": "missing", "role": "unknown"})
    assert response.status_code == 400


def test_session_requires_token(client):
    resume = client.post("/api/resumes", files={"file": ("resume.txt", b"Python project experience", "text/plain")})
    session = client.post("/api/sessions", json={"candidate_id": resume.json()["candidate_id"], "role": "ai-ml-engineer"})
    assert client.get(f"/api/sessions/{session.json()['session_id']}").status_code == 401
