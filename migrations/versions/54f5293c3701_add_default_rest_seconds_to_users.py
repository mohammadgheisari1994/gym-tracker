"""add default_rest_seconds to users

Revision ID: 54f5293c3701
Revises: eaccbf40bea8
Create Date: 2026-08-31 17:44:54.358325

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "54f5293c3701"
down_revision: str | None = "eaccbf40bea8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "default_rest_seconds",
            sa.Integer(),
            server_default=sa.text("120"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "default_rest_seconds")
