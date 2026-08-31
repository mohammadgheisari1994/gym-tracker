"""ORM models.

Import every model module here so that Alembic's autogenerate sees the full
metadata.
"""

from app.models.base import Base, TimestampMixin
from app.models.exercise import Exercise, MuscleGroup
from app.models.user import User

__all__ = ["Base", "Exercise", "MuscleGroup", "TimestampMixin", "User"]
