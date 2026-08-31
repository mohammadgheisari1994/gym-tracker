"""add exercise_guides table

Revision ID: c3f14b675659
Revises: 54f5293c3701
Create Date: 2026-08-31 18:01:51.168794

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3f14b675659"
down_revision: str | None = "54f5293c3701"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "exercise_guides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercises.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source_slugs", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("exercise_guides")
