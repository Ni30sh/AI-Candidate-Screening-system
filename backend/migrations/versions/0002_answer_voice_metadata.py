"""Add transcript and duration metadata to answers."""
from alembic import op
import sqlalchemy as sa

revision = "0002_answer_voice_metadata"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("answers", sa.Column("transcript", sa.Text(), nullable=True))
    op.add_column("answers", sa.Column("duration_seconds", sa.Float(), nullable=True))
    op.add_column("answers", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE answers SET transcript = answer")
    op.execute("UPDATE answers SET created_at = CURRENT_TIMESTAMP")
    with op.batch_alter_table("answers") as batch:
        batch.alter_column("transcript", nullable=False)
        batch.alter_column("created_at", nullable=False)


def downgrade() -> None:
    op.drop_column("answers", "created_at")
    op.drop_column("answers", "duration_seconds")
    op.drop_column("answers", "transcript")