"""Workout sessions, the exercises in them, and the sets logged against those."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SetType(StrEnum):
    NORMAL = "normal"
    WARMUP = "warmup"
    DROP = "drop"
    SUPERSET = "superset"
    FAILURE = "failure"


_SET_TYPE = Enum(
    SetType,
    native_enum=False,
    create_constraint=False,
    length=20,
    values_callable=lambda enum: [member.value for member in enum],
)


class Workout(TimestampMixin, Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    performed_on: Mapped[date] = mapped_column(Date, server_default=text("CURRENT_DATE"))
    title: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(String(2000))

    entries: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.position",
    )


class WorkoutExercise(TimestampMixin, Base):
    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, server_default=text("0"))

    workout: Mapped[Workout] = relationship(back_populates="entries")
    exercise: Mapped["object"] = relationship("Exercise")
    sets: Mapped[list["SetEntry"]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="SetEntry.position",
    )


class SetEntry(TimestampMixin, Base):
    __tablename__ = "set_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_exercises.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    reps: Mapped[int] = mapped_column(Integer)
    set_type: Mapped[SetType] = mapped_column(_SET_TYPE, server_default=text("'normal'"))
    rpe: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))

    entry: Mapped[WorkoutExercise] = relationship(back_populates="sets")
