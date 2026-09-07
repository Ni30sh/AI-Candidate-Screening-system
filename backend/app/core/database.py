from collections.abc import Generator
import hashlib
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import get_settings


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import answer, candidate, interview, question, report  # noqa: F401
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
        if settings.database_url.startswith("sqlite"):
            repair_legacy_sqlite_schema()


def repair_legacy_sqlite_schema() -> None:
    """Upgrade pre-Alembic local databases without deleting existing data."""
    inspector = inspect(engine)
    with engine.begin() as connection:
        session_columns = {column["name"] for column in inspector.get_columns("interview_sessions")}
        if "access_token_hash" not in session_columns:
            connection.execute(text("ALTER TABLE interview_sessions ADD COLUMN access_token_hash VARCHAR(64)"))
            rows = connection.execute(text("SELECT id FROM interview_sessions WHERE access_token_hash IS NULL")).fetchall()
            for row in rows:
                token_hash = hashlib.sha256(f"legacy:{row.id}".encode()).hexdigest()
                connection.execute(text("UPDATE interview_sessions SET access_token_hash = :token_hash WHERE id = :session_id"), {"token_hash": token_hash, "session_id": row.id})
        answer_columns = {column["name"] for column in inspector.get_columns("answers")}
        if "transcript" not in answer_columns:
            connection.execute(text("ALTER TABLE answers ADD COLUMN transcript TEXT"))
            connection.execute(text("UPDATE answers SET transcript = answer WHERE transcript IS NULL"))
        if "duration_seconds" not in answer_columns:
            connection.execute(text("ALTER TABLE answers ADD COLUMN duration_seconds FLOAT"))
        if "created_at" not in answer_columns:
            connection.execute(text("ALTER TABLE answers ADD COLUMN created_at DATETIME"))
            connection.execute(text("UPDATE answers SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
