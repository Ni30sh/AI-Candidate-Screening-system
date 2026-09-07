import re

SKILL_TERMS = ["Python", "Java", "C++", "JavaScript", "TypeScript", "SQL", "TensorFlow", "PyTorch", "Keras", "scikit-learn", "FastAPI", "Django", "React", "PostgreSQL", "MongoDB", "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Git", "Pandas", "NumPy", "OpenCV", "Spark", "Kafka", "REST", "GraphQL", "CNN", "RNN", "NLP", "LLM", "computer vision"]
DOMAIN_TERMS = ["machine learning", "deep learning", "data science", "natural language processing", "computer vision", "distributed systems", "cloud", "recommendation", "fraud", "time series", "analytics"]


def _present_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return [term for term in terms if re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", lowered)]


def analyze_resume(text: str) -> dict:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if len(part.strip()) > 30]
    skills = _present_terms(text, SKILL_TERMS)
    domains = _present_terms(text, DOMAIN_TERMS)
    projects = [sentence for sentence in sentences if re.search(r"project|built|developed|implemented|experience", sentence, re.I)][:8]
    return {"skills": skills, "technologies": skills, "domains": domains, "projects": projects}
