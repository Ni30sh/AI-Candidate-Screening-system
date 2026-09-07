"""Create initial interview schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("candidates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("resume_info", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"))
    op.create_table("interview_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("access_token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_interview_sessions_candidate_id", "interview_sessions", ["candidate_id"])
    op.create_index("ix_interview_sessions_role", "interview_sessions", ["role"])
    op.create_index("ix_interview_sessions_status", "interview_sessions", ["status"])
    op.create_index("ix_session_candidate_status", "interview_sessions", ["candidate_id", "status"])
    op.create_index("ix_interview_sessions_access_token_hash", "interview_sessions", ["access_token_hash"], unique=True)
    op.create_table("questions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("question_type", sa.String(length=30), nullable=False),
        sa.Column("retrieved_context", sa.JSON(), nullable=False),
        sa.Column("generation_trace", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_questions_session_id", "questions", ["session_id"])
    op.create_table("answers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("evaluation", sa.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("question_id"))
    op.create_table("reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("session_id"))


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("answers")
    op.drop_index("ix_questions_session_id", table_name="questions")
    op.drop_table("questions")
    op.drop_index("ix_interview_sessions_access_token_hash", table_name="interview_sessions")
    op.drop_index("ix_session_candidate_status", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_status", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_role", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_candidate_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    op.drop_table("candidates")
