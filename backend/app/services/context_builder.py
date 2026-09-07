from app.schemas.api import Role


def build_context(resume_info: dict, role: Role, question_number: int) -> dict:
    skills = resume_info.get("skills", [])
    domains = resume_info.get("domains", [])
    topics = list(dict.fromkeys(domains + skills))
    role_topics = {
        "ai-ml-engineer": ["model evaluation", "generalization", "deployment"],
        "backend-engineer": ["API design", "data modeling", "reliability"],
        "data-science-applied-ml": ["experimentation", "feature engineering", "model interpretation"],
    }.get(role.id, [])
    topics = (topics + role_topics) or role_topics
    topic = topics[(question_number - 1) % len(topics)]
    query = f"{role.name} interview topic {topic}; candidate experience in {' '.join(skills[:8])}"
    return {"topics": topics, "topic": topic, "query": query, "role": role.name}
