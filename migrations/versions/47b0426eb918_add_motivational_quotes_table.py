"""add motivational_quotes table

Revision ID: 47b0426eb918
Revises: a59c738f5be0
Create Date: 2026-08-31 18:18:57.448963

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "47b0426eb918"
down_revision: str | None = "a59c738f5be0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "motivational_quotes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("for_date", sa.Date(), nullable=False),
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
    op.drop_table("motivational_quotes")
