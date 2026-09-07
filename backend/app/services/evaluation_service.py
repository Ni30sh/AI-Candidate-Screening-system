from app.services.llm_service import evaluate_answer_with_llm


def evaluate_answer(answer: str, question: dict, role: str = "", retrieved: list[dict] | None = None) -> dict:
    generated = evaluate_answer_with_llm(role, question, answer, retrieved or [])
    if generated:
        return generated.model_dump()
    words = len(answer.split())
    score = min(10.0, round(2 + words / 35, 1)) if words else 0
    return {"score": score, "feedback": "Answer captured for review." if words < 25 else "Answer shows a substantive explanation; add concrete trade-offs and validation details where possible.", "word_count": words}


def build_report(questions: list) -> tuple[str, dict]:
    evaluations = [question.answer.evaluation for question in questions if question.answer]
    scores = [item.get("score", 0) for item in evaluations]
    by_topic: dict[str, list[float]] = {}
    for question in questions:
        if question.answer:
            by_topic.setdefault(question.topic, []).append(question.answer.score)
    topic_scores = {topic: round(sum(values) / len(values), 1) for topic, values in by_topic.items()}
    overall = round(sum(scores) / len(scores), 1) if scores else 0
    strengths = [topic for topic, score in topic_scores.items() if score >= 6]
    improvements = [topic for topic, score in topic_scores.items() if score < 6]
    summary = f"Overall performance: {overall}/10 across {len(evaluations)} answered questions."
    return summary, {"overall_score": overall, "topic_scores": topic_scores, "strengths": strengths, "areas_for_improvement": improvements}
