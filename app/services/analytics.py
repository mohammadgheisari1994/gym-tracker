"""Progress analytics computed from a user's logged sets.

Each function runs one query and aggregates in Python; a personal training log
is small enough that this stays simple and database-agnostic.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Exercise,
    MuscleGroup,
    SetEntry,
    User,
    Workout,
    WorkoutExercise,
)
from app.services.one_rep_max import epley_one_rep_max

_ZERO = Decimal("0")


@dataclass(frozen=True)
class ExercisePoint:
    on: date
    top_weight: Decimal | None
    volume: Decimal
    reps: int
    best_e1rm: Decimal | None


@dataclass(frozen=True)
class MuscleVolume:
    muscle_group: MuscleGroup
    volume: Decimal


@dataclass(frozen=True)
class OverallStats:
    window_weeks: int
    total_workouts: int
    total_volume: Decimal
    weekly_volume: list[tuple[str, Decimal]]
    weekly_frequency: list[tuple[str, int]]
    muscle_distribution: list[MuscleVolume]

    @property
    def has_data(self) -> bool:
        return self.total_workouts > 0


def _week_label(day: date) -> str:
    iso = day.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _week_labels(start: date, end: date) -> list[str]:
    monday = start - timedelta(days=start.weekday())
    last_monday = end - timedelta(days=end.weekday())
    labels: list[str] = []
    while monday <= last_monday:
        labels.append(_week_label(monday))
        monday += timedelta(days=7)
    return labels


def exercise_progress(session: Session, exercise: Exercise) -> list[ExercisePoint]:
    """One point per workout date on which ``exercise`` was trained."""
    rows = session.execute(
        select(Workout.performed_on, SetEntry.weight, SetEntry.reps)
        .join(WorkoutExercise, WorkoutExercise.workout_id == Workout.id)
        .join(SetEntry, SetEntry.workout_exercise_id == WorkoutExercise.id)
        .where(WorkoutExercise.exercise_id == exercise.id)
    ).all()

    by_day: dict[date, list[tuple[Decimal | None, int]]] = defaultdict(list)
    for performed_on, weight, reps in rows:
        by_day[performed_on].append((weight, reps))

    points: list[ExercisePoint] = []
    for day in sorted(by_day):
        sets = by_day[day]
        weighted = [(w, r) for w, r in sets if w is not None]
        points.append(
            ExercisePoint(
                on=day,
                top_weight=max((w for w, _ in weighted), default=None),
                volume=sum((w * r for w, r in weighted), _ZERO),
                reps=sum(r for _, r in sets),
                best_e1rm=max(
                    (epley_one_rep_max(w, r) for w, r in weighted),
                    default=None,
                ),
            )
        )
    return points


def overall_stats(session: Session, user: User, *, weeks: int = 12) -> OverallStats:
    today = date.today()
    cutoff = today - timedelta(weeks=weeks)

    rows = session.execute(
        select(
            Workout.id,
            Workout.performed_on,
            SetEntry.weight,
            SetEntry.reps,
            Exercise.muscle_group,
        )
        .join(WorkoutExercise, WorkoutExercise.workout_id == Workout.id)
        .join(Exercise, Exercise.id == WorkoutExercise.exercise_id)
        .join(SetEntry, SetEntry.workout_exercise_id == WorkoutExercise.id)
        .where(Workout.user_id == user.id, Workout.performed_on >= cutoff)
    ).all()

    volume_by_week: dict[str, Decimal] = defaultdict(lambda: _ZERO)
    workouts_by_week: dict[str, set[int]] = defaultdict(set)
    volume_by_muscle: dict[MuscleGroup, Decimal] = defaultdict(lambda: _ZERO)
    all_workouts: set[int] = set()
    total_volume = _ZERO

    for workout_id, performed_on, weight, reps, muscle_group in rows:
        label = _week_label(performed_on)
        workouts_by_week[label].add(workout_id)
        all_workouts.add(workout_id)
        if weight is not None:
            contribution = weight * reps
            volume_by_week[label] += contribution
            volume_by_muscle[MuscleGroup(muscle_group)] += contribution
            total_volume += contribution

    labels = _week_labels(cutoff, today)
    return OverallStats(
        window_weeks=weeks,
        total_workouts=len(all_workouts),
        total_volume=total_volume,
        weekly_volume=[(label, volume_by_week[label]) for label in labels],
        weekly_frequency=[(label, len(workouts_by_week[label])) for label in labels],
        muscle_distribution=sorted(
            (MuscleVolume(mg, vol) for mg, vol in volume_by_muscle.items() if vol > 0),
            key=lambda mv: mv.volume,
            reverse=True,
        ),
    )
