"""create exercises table

Revision ID: 20167fa97d2a
Revises: 0d062f1431da
Create Date: 2026-08-31 17:00:22.198825

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20167fa97d2a"
down_revision: str | None = "0d062f1431da"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "muscle_group",
            sa.String(length=20),
            server_default=sa.text("'other'"),
            nullable=False,
        ),
        sa.Column("notes", sa.String(length=2000), nullable=True),
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
    op.create_index("ix_exercises_user_id", "exercises", ["user_id"])
    op.create_index(
        "uq_exercises_user_name",
        "exercises",
        ["user_id", sa.text("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_exercises_user_name", table_name="exercises")
    op.drop_index("ix_exercises_user_id", table_name="exercises")
    op.drop_table("exercises")
