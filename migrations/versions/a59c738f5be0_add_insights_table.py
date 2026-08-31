"""add insights table

Revision ID: a59c738f5be0
Revises: c3f14b675659
Create Date: 2026-08-31 18:11:54.795257

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a59c738f5be0"
down_revision: str | None = "c3f14b675659"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "insights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scope", sa.String(length=40), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data_signature", sa.String(length=32), nullable=False),
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
        sa.UniqueConstraint("user_id", "scope", name="uq_insights_user_scope"),
    )
    op.create_index("ix_insights_user_id", "insights", ["user_id"])


def downgrade() -> None:
    op.drop_table("insights")
