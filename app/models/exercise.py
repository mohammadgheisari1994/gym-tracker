"""User-owned exercise catalogue."""

from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MuscleGroup(StrEnum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    CORE = "core"
    OTHER = "other"


# Stored as VARCHAR(20) (no DB CHECK); SQLAlchemy coerces to/from the enum.
_MUSCLE_GROUP = Enum(
    MuscleGroup,
    native_enum=False,
    create_constraint=False,
    length=20,
    values_callable=lambda enum: [member.value for member in enum],
)


class Exercise(TimestampMixin, Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    muscle_group: Mapped[MuscleGroup] = mapped_column(_MUSCLE_GROUP, server_default=text("'other'"))
    notes: Mapped[str | None] = mapped_column(String(2000))

    user: Mapped["object"] = relationship("User")


# Case-insensitive uniqueness of an exercise name within one user's catalogue.
Index(
    "uq_exercises_user_name",
    Exercise.user_id,
    func.lower(Exercise.name),
    unique=True,
)
