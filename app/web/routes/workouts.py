"""Workout logging: sessions, their exercises, and sets."""

from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.models import SetType
from app.services.exercises import list_exercises
from app.services.workouts import (
    add_exercise,
    add_set,
    create_workout,
    delete_workout,
    get_workout,
    last_set_for_entry,
    list_workouts,
    move_exercise,
    move_set,
    owned_entry,
    owned_set,
    remove_exercise,
    remove_set,
    update_set,
    update_workout,
)
from app.web.deps import DbSession, RequiredUser, set_flash
from app.web.forms import SetForm, WorkoutForm
from app.web.templating import render

router = APIRouter(tags=["workouts"])

_SET_TYPES = tuple(SetType)


def _back_to(workout_id: int, entry_id: int | None = None) -> RedirectResponse:
    anchor = f"#entry-{entry_id}" if entry_id else ""
    return RedirectResponse(url=f"/workouts/{workout_id}{anchor}", status_code=303)


# --- workout list / CRUD ---------------------------------------------------


@router.get("/workouts")
def index(request: Request, session: DbSession, user: RequiredUser):
    return render(
        request,
        "workouts/list.html",
        {"workouts": list_workouts(session, user)},
        user=user,
    )


@router.get("/workouts/new")
def new_form(request: Request, user: RequiredUser):
    return render(
        request,
        "workouts/form.html",
        {"action": "/workouts", "values": {"performed_on": date.today().isoformat()}},
        user=user,
    )


@router.post("/workouts")
async def create(request: Request, session: DbSession, user: RequiredUser):
    raw = dict(await request.form())
    try:
        form = WorkoutForm.model_validate(raw)
    except ValidationError:
        set_flash(request, "workouts.error.invalid_date", level="error")
        return RedirectResponse(url="/workouts/new", status_code=303)

    workout = create_workout(
        session,
        user,
        performed_on=form.performed_on,
        title=form.title,
        notes=form.notes,
    )
    session.commit()
    return _back_to(workout.id)


@router.get("/workouts/{workout_id}")
def detail(request: Request, session: DbSession, user: RequiredUser, workout_id: int):
    workout = get_workout(session, user, workout_id)
    prefill = {entry.id: last_set_for_entry(session, entry) for entry in workout.entries}
    return render(
        request,
        "workouts/detail.html",
        {
            "workout": workout,
            "catalogue": list_exercises(session, user),
            "set_types": _SET_TYPES,
            "prefill": prefill,
        },
        user=user,
    )


@router.get("/workouts/{workout_id}/edit")
def edit_form(request: Request, session: DbSession, user: RequiredUser, workout_id: int):
    workout = get_workout(session, user, workout_id)
    return render(
        request,
        "workouts/form.html",
        {
            "action": f"/workouts/{workout.id}",
            "values": {
                "performed_on": workout.performed_on.isoformat(),
                "title": workout.title or "",
                "notes": workout.notes or "",
            },
        },
        user=user,
    )


@router.post("/workouts/{workout_id}")
async def update(request: Request, session: DbSession, user: RequiredUser, workout_id: int):
    raw = dict(await request.form())
    try:
        form = WorkoutForm.model_validate(raw)
    except ValidationError:
        set_flash(request, "workouts.error.invalid_date", level="error")
        return RedirectResponse(url=f"/workouts/{workout_id}/edit", status_code=303)

    update_workout(
        session,
        user,
        workout_id,
        performed_on=form.performed_on,
        title=form.title,
        notes=form.notes,
    )
    session.commit()
    set_flash(request, "workouts.saved")
    return _back_to(workout_id)


@router.post("/workouts/{workout_id}/delete")
def delete(request: Request, session: DbSession, user: RequiredUser, workout_id: int):
    delete_workout(session, user, workout_id)
    session.commit()
    set_flash(request, "workouts.deleted")
    return RedirectResponse(url="/workouts", status_code=303)


# --- exercises within a workout ------------------------------------------


@router.post("/workouts/{workout_id}/exercises")
async def add_workout_exercise(
    request: Request, session: DbSession, user: RequiredUser, workout_id: int
):
    raw = dict(await request.form())
    try:
        exercise_id = int(raw.get("exercise_id", ""))
    except ValueError:
        set_flash(request, "workouts.error.pick_exercise", level="error")
        return _back_to(workout_id)

    entry = add_exercise(session, user, workout_id, exercise_id)
    session.commit()
    return _back_to(workout_id, entry.id)


@router.post("/workout-exercises/{entry_id}/delete")
def delete_workout_exercise(
    request: Request, session: DbSession, user: RequiredUser, entry_id: int
):
    workout_id = owned_entry(session, user, entry_id).workout_id
    remove_exercise(session, user, entry_id)
    session.commit()
    return RedirectResponse(url=f"/workouts/{workout_id}", status_code=303)


@router.post("/workout-exercises/{entry_id}/move")
async def move_workout_exercise(
    request: Request, session: DbSession, user: RequiredUser, entry_id: int
):
    workout_id = owned_entry(session, user, entry_id).workout_id
    move_exercise(session, user, entry_id, _direction(dict(await request.form())))
    session.commit()
    return _back_to(workout_id, entry_id)


# --- sets ---------------------------------------------------------------


@router.post("/workout-exercises/{entry_id}/sets")
async def create_set(request: Request, session: DbSession, user: RequiredUser, entry_id: int):
    workout_id = owned_entry(session, user, entry_id).workout_id
    raw = dict(await request.form())
    try:
        form = SetForm.model_validate(raw)
    except ValidationError:
        set_flash(request, "sets.error.invalid", level="error")
        return _back_to(workout_id, entry_id)

    add_set(
        session,
        user,
        entry_id,
        weight=form.weight,
        reps=form.reps,
        set_type=form.set_type,
        rpe=form.rpe,
    )
    session.commit()
    return _back_to(workout_id, entry_id)


@router.post("/sets/{set_id}")
async def edit_set(request: Request, session: DbSession, user: RequiredUser, set_id: int):
    workout_id, entry_id = _set_location(session, user, set_id)
    raw = dict(await request.form())
    try:
        form = SetForm.model_validate(raw)
    except ValidationError:
        set_flash(request, "sets.error.invalid", level="error")
        return _back_to(workout_id, entry_id)

    update_set(
        session,
        user,
        set_id,
        weight=form.weight,
        reps=form.reps,
        set_type=form.set_type,
        rpe=form.rpe,
    )
    session.commit()
    return _back_to(workout_id, entry_id)


@router.post("/sets/{set_id}/delete")
def delete_set(request: Request, session: DbSession, user: RequiredUser, set_id: int):
    workout_id, entry_id = _set_location(session, user, set_id)
    remove_set(session, user, set_id)
    session.commit()
    return _back_to(workout_id, entry_id)


@router.post("/sets/{set_id}/move")
async def reorder_set(request: Request, session: DbSession, user: RequiredUser, set_id: int):
    workout_id, entry_id = _set_location(session, user, set_id)
    move_set(session, user, set_id, _direction(dict(await request.form())))
    session.commit()
    return _back_to(workout_id, entry_id)


# --- small route helpers ------------------------------------------------


def _set_location(session, user, set_id: int) -> tuple[int, int]:
    """Return ``(workout_id, entry_id)`` for a set the user owns."""
    set_entry = owned_set(session, user, set_id)
    return set_entry.entry.workout_id, set_entry.workout_exercise_id


def _direction(raw: dict) -> str:
    return "up" if raw.get("direction") == "up" else "down"
