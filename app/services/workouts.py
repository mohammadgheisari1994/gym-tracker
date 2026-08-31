"""Workout logging: sessions, their exercises, and the sets within them.

Every function takes the acting user. Ownership is enforced by joining back to
``workouts.user_id`` — no endpoint trusts a client-supplied owner.
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Exercise,
    SetEntry,
    SetType,
    User,
    Workout,
    WorkoutExercise,
)
from app.services.errors import ResourceNotFound

Direction = Literal["up", "down"]


# --- lookups -----------------------------------------------------------------


def list_workouts(session: Session, user: User) -> list[Workout]:
    stmt = (
        select(Workout)
        .where(Workout.user_id == user.id)
        .order_by(Workout.performed_on.desc(), Workout.id.desc())
    )
    return list(session.scalars(stmt))


def get_workout(session: Session, user: User, workout_id: int) -> Workout:
    stmt = (
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == user.id)
        .options(
            selectinload(Workout.entries).selectinload(WorkoutExercise.exercise),
            selectinload(Workout.entries).selectinload(WorkoutExercise.sets),
        )
    )
    workout = session.scalar(stmt)
    if workout is None:
        raise ResourceNotFound
    return workout


def owned_entry(session: Session, user: User, entry_id: int) -> WorkoutExercise:
    stmt = (
        select(WorkoutExercise)
        .join(Workout)
        .where(WorkoutExercise.id == entry_id, Workout.user_id == user.id)
    )
    entry = session.scalar(stmt)
    if entry is None:
        raise ResourceNotFound
    return entry


def owned_set(session: Session, user: User, set_id: int) -> SetEntry:
    stmt = (
        select(SetEntry)
        .join(WorkoutExercise)
        .join(Workout)
        .where(SetEntry.id == set_id, Workout.user_id == user.id)
    )
    set_entry = session.scalar(stmt)
    if set_entry is None:
        raise ResourceNotFound
    return set_entry


# --- workout CRUD -----------------------------------------------------------


def create_workout(
    session: Session,
    user: User,
    *,
    performed_on: date,
    title: str | None,
    notes: str | None,
) -> Workout:
    workout = Workout(
        user_id=user.id,
        performed_on=performed_on,
        title=_clean(title),
        notes=_clean(notes),
    )
    session.add(workout)
    session.flush()
    return workout


def update_workout(
    session: Session,
    user: User,
    workout_id: int,
    *,
    performed_on: date,
    title: str | None,
    notes: str | None,
) -> Workout:
    workout = get_workout(session, user, workout_id)
    workout.performed_on = performed_on
    workout.title = _clean(title)
    workout.notes = _clean(notes)
    session.add(workout)
    return workout


def delete_workout(session: Session, user: User, workout_id: int) -> None:
    session.delete(get_workout(session, user, workout_id))


# --- exercises within a workout --------------------------------------------


def add_exercise(
    session: Session, user: User, workout_id: int, exercise_id: int
) -> WorkoutExercise:
    workout = get_workout(session, user, workout_id)
    exercise = session.get(Exercise, exercise_id)
    if exercise is None or exercise.user_id != user.id:
        raise ResourceNotFound

    entry = WorkoutExercise(
        workout_id=workout.id,
        exercise_id=exercise.id,
        position=_next_position(session, WorkoutExercise, WorkoutExercise.workout_id, workout.id),
    )
    session.add(entry)
    session.flush()
    return entry


def remove_exercise(session: Session, user: User, entry_id: int) -> None:
    session.delete(owned_entry(session, user, entry_id))


def move_exercise(session: Session, user: User, entry_id: int, direction: Direction) -> None:
    entry = owned_entry(session, user, entry_id)
    _swap_with_neighbour(session, WorkoutExercise, WorkoutExercise.workout_id, entry, direction)


# --- sets ------------------------------------------------------------------


def add_set(
    session: Session,
    user: User,
    entry_id: int,
    *,
    weight: Decimal | None,
    reps: int,
    set_type: SetType,
    rpe: Decimal | None,
) -> SetEntry:
    entry = owned_entry(session, user, entry_id)
    set_entry = SetEntry(
        workout_exercise_id=entry.id,
        position=_next_position(session, SetEntry, SetEntry.workout_exercise_id, entry.id),
        weight=weight,
        reps=reps,
        set_type=set_type,
        rpe=rpe,
    )
    session.add(set_entry)
    session.flush()
    return set_entry


def update_set(
    session: Session,
    user: User,
    set_id: int,
    *,
    weight: Decimal | None,
    reps: int,
    set_type: SetType,
    rpe: Decimal | None,
) -> SetEntry:
    set_entry = owned_set(session, user, set_id)
    set_entry.weight = weight
    set_entry.reps = reps
    set_entry.set_type = set_type
    set_entry.rpe = rpe
    session.add(set_entry)
    return set_entry


def remove_set(session: Session, user: User, set_id: int) -> None:
    session.delete(owned_set(session, user, set_id))


def move_set(session: Session, user: User, set_id: int, direction: Direction) -> None:
    set_entry = owned_set(session, user, set_id)
    _swap_with_neighbour(session, SetEntry, SetEntry.workout_exercise_id, set_entry, direction)


def last_set_for_entry(session: Session, entry: WorkoutExercise) -> SetEntry | None:
    """The most recently ordered set, used to pre-fill the add-set form."""
    stmt = (
        select(SetEntry)
        .where(SetEntry.workout_exercise_id == entry.id)
        .order_by(SetEntry.position.desc())
        .limit(1)
    )
    return session.scalar(stmt)


# --- helpers --------------------------------------------------------------


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _next_position(session: Session, model, parent_column, parent_id: int) -> int:
    current_max = session.scalar(select(func.max(model.position)).where(parent_column == parent_id))
    return 0 if current_max is None else current_max + 1


def _swap_with_neighbour(session, model, parent_column, item, direction: Direction) -> None:
    parent_id = getattr(item, parent_column.key)
    if direction == "up":
        neighbour_stmt = (
            select(model)
            .where(parent_column == parent_id, model.position < item.position)
            .order_by(model.position.desc())
            .limit(1)
        )
    else:
        neighbour_stmt = (
            select(model)
            .where(parent_column == parent_id, model.position > item.position)
            .order_by(model.position.asc())
            .limit(1)
        )

    neighbour = session.scalar(neighbour_stmt)
    if neighbour is None:
        return

    item.position, neighbour.position = neighbour.position, item.position
    session.add_all([item, neighbour])
