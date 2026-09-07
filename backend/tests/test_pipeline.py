from app.services.context_builder import build_context
from app.services.evaluation_service import build_report
from app.services.resume_analyzer import analyze_resume
from app.services.resume_parser import clean_text, extract_resume
from app.services.retriever import LocalRetriever
from app.services.roles import get_role


def test_resume_parsing_and_analysis():
    text = extract_resume("resume.txt", b"  Python   TensorFlow project. Experience with machine learning and FastAPI. ")
    assert clean_text(text).startswith("Python TensorFlow")
    info = analyze_resume(text)
    assert "Python" in info["skills"]
    assert "machine learning" in info["domains"]


def test_retrieval_preserves_traceability(tmp_path):
    retriever = LocalRetriever(str(tmp_path / "index.pkl"))
    retriever.build([{"chunk_id": "c-1", "text": "CNN overfitting validation dropout", "source": "book.pdf", "role": "ai-ml-engineer", "page": 3, "section": "Regularization"}])
    results = retriever.search("CNN overfitting", "ai-ml-engineer")
    assert results[0]["chunk_id"] == "c-1"
    assert results[0]["source"] == "book.pdf"


def test_context_is_dynamic():
    context = build_context({"skills": ["TensorFlow"], "domains": ["computer vision"]}, get_role("ai-ml-engineer"), 1)
    assert "TensorFlow" in context["query"]
    assert context["topic"] != "Explain machine learning."


def test_report_is_structured():
    class Answer:
        score = 8
        evaluation = {"score": 8}
        answer = "A detailed answer"
    class Question:
        topic = "CNN"
        answer = Answer()
    summary, analysis = build_report([Question()])
    assert "8.0/10" in summary
    assert analysis["topic_scores"]["CNN"] == 8.0
