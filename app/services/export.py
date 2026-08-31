"""Export a user's data for backup or spreadsheet analysis."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Exercise, User, Workout, WorkoutExercise

CSV_COLUMNS = (
    "workout_date",
    "workout_title",
    "exercise",
    "muscle_group",
    "set_number",
    "set_type",
    "weight",
    "reps",
    "rpe",
)


def _num(value) -> float | None:
    return float(value) if value is not None else None


def _load_workouts(session: Session, user: User) -> list[Workout]:
    stmt = (
        select(Workout)
        .where(Workout.user_id == user.id)
        .order_by(Workout.performed_on, Workout.id)
        .options(
            selectinload(Workout.entries).selectinload(WorkoutExercise.exercise),
            selectinload(Workout.entries).selectinload(WorkoutExercise.sets),
        )
    )
    return list(session.scalars(stmt))


def workout_rows(session: Session, user: User) -> list[dict[str, Any]]:
    """One flat record per logged set."""
    rows: list[dict[str, Any]] = []
    for workout in _load_workouts(session, user):
        for entry in workout.entries:
            for index, set_entry in enumerate(entry.sets, start=1):
                rows.append(
                    {
                        "workout_date": workout.performed_on.isoformat(),
                        "workout_title": workout.title or "",
                        "exercise": entry.exercise.name,
                        "muscle_group": entry.exercise.muscle_group.value,
                        "set_number": index,
                        "set_type": set_entry.set_type.value,
                        "weight": _num(set_entry.weight),
                        "reps": set_entry.reps,
                        "rpe": _num(set_entry.rpe),
                    }
                )
    return rows


def full_export(session: Session, user: User) -> dict[str, Any]:
    """A complete, nested snapshot of the user's data."""
    exercises = session.scalars(
        select(Exercise).where(Exercise.user_id == user.id).order_by(Exercise.name)
    )

    return {
        "profile": {
            "display_name": user.display_name,
            "email": user.email,
            "preferred_language": user.preferred_language,
            "weight_unit": user.weight_unit.value,
            "default_rest_seconds": user.default_rest_seconds,
        },
        "exercises": [
            {
                "name": exercise.name,
                "muscle_group": exercise.muscle_group.value,
                "notes": exercise.notes,
            }
            for exercise in exercises
        ],
        "workouts": [
            {
                "date": workout.performed_on.isoformat(),
                "title": workout.title,
                "notes": workout.notes,
                "exercises": [
                    {
                        "name": entry.exercise.name,
                        "sets": [
                            {
                                "type": set_entry.set_type.value,
                                "weight": _num(set_entry.weight),
                                "reps": set_entry.reps,
                                "rpe": _num(set_entry.rpe),
                            }
                            for set_entry in entry.sets
                        ],
                    }
                    for entry in workout.entries
                ],
            }
            for workout in _load_workouts(session, user)
        ],
    }
