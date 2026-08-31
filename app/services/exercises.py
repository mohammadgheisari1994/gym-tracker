"""CRUD for a user's personal exercise catalogue.

Every function takes the acting user and scopes all queries to them.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Exercise, MuscleGroup, User
from app.services.errors import DuplicateExercise, ResourceNotFound


def list_exercises(session: Session, user: User) -> list[Exercise]:
    stmt = select(Exercise).where(Exercise.user_id == user.id).order_by(func.lower(Exercise.name))
    return list(session.scalars(stmt))


def get_exercise(session: Session, user: User, exercise_id: int) -> Exercise:
    exercise = session.get(Exercise, exercise_id)
    if exercise is None or exercise.user_id != user.id:
        raise ResourceNotFound
    return exercise


def _name_taken(session: Session, user: User, name: str, *, exclude_id: int | None = None) -> bool:
    stmt = select(Exercise.id).where(
        Exercise.user_id == user.id,
        func.lower(Exercise.name) == name.strip().lower(),
    )
    if exclude_id is not None:
        stmt = stmt.where(Exercise.id != exclude_id)
    return session.scalar(stmt) is not None


def create_exercise(
    session: Session,
    user: User,
    *,
    name: str,
    muscle_group: MuscleGroup,
    notes: str | None,
) -> Exercise:
    if _name_taken(session, user, name):
        raise DuplicateExercise

    exercise = Exercise(
        user_id=user.id,
        name=name.strip(),
        muscle_group=muscle_group,
        notes=(notes.strip() or None) if notes else None,
    )
    session.add(exercise)
    session.flush()
    return exercise


def update_exercise(
    session: Session,
    user: User,
    exercise_id: int,
    *,
    name: str,
    muscle_group: MuscleGroup,
    notes: str | None,
) -> Exercise:
    exercise = get_exercise(session, user, exercise_id)
    if _name_taken(session, user, name, exclude_id=exercise.id):
        raise DuplicateExercise

    exercise.name = name.strip()
    exercise.muscle_group = muscle_group
    exercise.notes = (notes.strip() or None) if notes else None
    session.add(exercise)
    return exercise


def delete_exercise(session: Session, user: User, exercise_id: int) -> None:
    session.delete(get_exercise(session, user, exercise_id))
