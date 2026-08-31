"""add weight_unit and workout logging tables

Revision ID: eaccbf40bea8
Revises: 20167fa97d2a
Create Date: 2026-08-31 17:16:28.370807

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "eaccbf40bea8"
down_revision: str | None = "20167fa97d2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SET_TYPE = sa.Enum(
    "normal",
    "warmup",
    "drop",
    "superset",
    "failure",
    name="settype",
    native_enum=False,
    length=20,
)
_WEIGHT_UNIT = sa.Enum("kg", "lb", name="weightunit", native_enum=False, length=4)

_TIMESTAMPS = (
    sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "weight_unit",
            _WEIGHT_UNIT,
            server_default=sa.text("'kg'"),
            nullable=False,
        ),
    )

    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "performed_on",
            sa.Date(),
            server_default=sa.text("CURRENT_DATE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        *_TIMESTAMPS,
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"])

    op.create_table(
        "workout_exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "workout_id",
            sa.Integer(),
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercises.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
        *_TIMESTAMPS,
    )
    op.create_index("ix_workout_exercises_workout_id", "workout_exercises", ["workout_id"])
    op.create_index("ix_workout_exercises_exercise_id", "workout_exercises", ["exercise_id"])

    op.create_table(
        "set_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "workout_exercise_id",
            sa.Integer(),
            sa.ForeignKey("workout_exercises.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("weight", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column(
            "set_type",
            _SET_TYPE,
            server_default=sa.text("'normal'"),
            nullable=False,
        ),
        sa.Column("rpe", sa.Numeric(precision=3, scale=1), nullable=True),
        *_TIMESTAMPS,
    )
    op.create_index("ix_set_entries_workout_exercise_id", "set_entries", ["workout_exercise_id"])


def downgrade() -> None:
    op.drop_table("set_entries")
    op.drop_table("workout_exercises")
    op.drop_table("workouts")
    op.drop_column("users", "weight_unit")
