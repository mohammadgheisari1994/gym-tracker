"""ORM models.

Import every model module here so that Alembic's autogenerate sees the full
metadata.
"""

from app.models.base import Base, TimestampMixin
from app.models.exercise import (
    Exercise,
    ExerciseGuide,
    ExerciseVideo,
    MuscleGroup,
)
from app.models.insight import Insight
from app.models.motivation import MotivationalQuote
from app.models.user import User, WeightUnit
from app.models.workout import SetEntry, SetType, Workout, WorkoutExercise

__all__ = [
    "Base",
    "Exercise",
    "ExerciseGuide",
    "ExerciseVideo",
    "Insight",
    "MotivationalQuote",
    "MuscleGroup",
    "SetEntry",
    "SetType",
    "TimestampMixin",
    "User",
    "WeightUnit",
    "Workout",
    "WorkoutExercise",
]
