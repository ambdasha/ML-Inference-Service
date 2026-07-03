"""add match history

Revision ID: 0002_match_history
Revises: 0001_initial
Create Date: 2026-07-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_match_history"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "match_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("vacancy_text", sa.Text(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("category_match", sa.Boolean(), nullable=False),
        sa.Column("level_match", sa.Boolean(), nullable=False),
        sa.Column("matched_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("extra_resume_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("resume_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("vacancy_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_index(
        "ix_match_history_user_id",
        "match_history",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_match_history_user_id", table_name="match_history")
    op.drop_table("match_history")