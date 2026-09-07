from app.schemas.api import Role

ROLES = {
    "ai-ml-engineer": Role(id="ai-ml-engineer", name="AI/ML Engineer", description="Machine learning systems, deep learning, and production inference."),
    "backend-engineer": Role(id="backend-engineer", name="Backend Engineer", description="Reliable APIs, data systems, distributed services, and testing."),
    "data-science-applied-ml": Role(id="data-science-applied-ml", name="Data Science / Applied ML", description="Statistical reasoning, experimentation, modeling, and communication."),
}


def get_role(role_id: str) -> Role:
    role = ROLES.get(role_id)
    if not role:
        raise ValueError(f"Unsupported role: {role_id}")
    return role
