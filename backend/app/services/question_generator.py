from app.services.llm_service import generate_question_with_llm


def generate_question(role: str, resume_info: dict, context: dict, retrieved: list[dict], question_number: int) -> dict:
    generated = generate_question_with_llm(role, resume_info, context, retrieved)
    if generated:
        return {**generated.model_dump(), "source_chunks": [item["chunk_id"] for item in retrieved], "grounding_excerpt": retrieved[0]["text"][:240] if retrieved else ""}
    skills = ", ".join(resume_info.get("skills", [])[:5]) or "the candidate's stated experience"
    topic = context["topic"]
    if retrieved:
        grounding = retrieved[0]["text"][:240].replace("\n", " ")
        question = f"For the {topic} work reflected in your background ({skills}), explain the design or trade-offs you would make in this situation. Ground your answer in the relevant principles from the knowledge base, and describe how you would validate the result."
    else:
        grounding = "No indexed context was available for this topic."
        question = f"As a {role}, explain how you would approach {topic} in a real project, including trade-offs and validation steps."
    difficulty = "medium" if question_number < 4 else "hard"
    return {"question": question, "topic": topic, "difficulty": difficulty, "question_type": "applied", "source_chunks": [item["chunk_id"] for item in retrieved], "grounding_excerpt": grounding}
