"""User-owned exercise catalogue."""

from enum import StrEnum

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text, func, text
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
    guide: Mapped["ExerciseGuide | None"] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        uselist=False,
    )
    video: Mapped["ExerciseVideo | None"] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ExerciseGuide(TimestampMixin, Base):
    """An LLM-generated execution guide, cached permanently per exercise."""

    __tablename__ = "exercise_guides"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), unique=True
    )
    body: Mapped[str] = mapped_column(Text)
    source_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))

    exercise: Mapped[Exercise] = relationship(back_populates="guide")


class ExerciseVideo(TimestampMixin, Base):
    """An instructional video, embedded through YouTube's official player."""

    __tablename__ = "exercise_videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), unique=True
    )
    youtube_id: Mapped[str] = mapped_column(String(20))
    title: Mapped[str | None] = mapped_column(String(200))
    # "seed" (from the curated list) or "manual" (the user pasted a URL)
    source: Mapped[str] = mapped_column(String(10))

    exercise: Mapped[Exercise] = relationship(back_populates="video")


# Case-insensitive uniqueness of an exercise name within one user's catalogue.
Index(
    "uq_exercises_user_name",
    Exercise.user_id,
    func.lower(Exercise.name),
    unique=True,
)
