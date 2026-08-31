"""The personal exercise catalogue."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.models import MuscleGroup
from app.services.errors import DuplicateExercise, ExerciseInUse
from app.services.exercises import (
    create_exercise,
    delete_exercise,
    get_exercise,
    list_exercises,
    update_exercise,
)
from app.web.deps import DbSession, RequiredUser, set_flash
from app.web.forms import ExerciseForm
from app.web.templating import render

router = APIRouter(tags=["exercises"], prefix="/exercises")

_MUSCLE_GROUPS = tuple(MuscleGroup)


def _form_page(
    request: Request,
    user,
    *,
    action: str,
    values: dict,
    errors: list[str],
    status_code: int = 200,
):
    return render(
        request,
        "exercises/form.html",
        {
            "action": action,
            "values": values,
            "errors": errors,
            "muscle_groups": _MUSCLE_GROUPS,
        },
        user=user,
        status_code=status_code,
    )


@router.get("")
def index(request: Request, session: DbSession, user: RequiredUser):
    return render(
        request,
        "exercises/list.html",
        {"exercises": list_exercises(session, user)},
        user=user,
    )


@router.get("/new")
def new_form(request: Request, user: RequiredUser):
    return _form_page(
        request,
        user,
        action="/exercises",
        values={"muscle_group": "other"},
        errors=[],
    )


@router.post("")
async def create(request: Request, session: DbSession, user: RequiredUser):
    raw = dict(await request.form())
    try:
        form = ExerciseForm.model_validate(raw)
    except ValidationError:
        return _form_page(
            request,
            user,
            action="/exercises",
            values=raw,
            errors=["exercises.error.name_required"],
            status_code=400,
        )

    try:
        create_exercise(
            session,
            user,
            name=form.name,
            muscle_group=form.muscle_group,
            notes=form.notes,
        )
    except DuplicateExercise:
        return _form_page(
            request,
            user,
            action="/exercises",
            values=raw,
            errors=["exercises.error.duplicate"],
            status_code=409,
        )

    session.commit()
    set_flash(request, "exercises.saved")
    return RedirectResponse(url="/exercises", status_code=303)


@router.get("/{exercise_id}/edit")
def edit_form(request: Request, session: DbSession, user: RequiredUser, exercise_id: int):
    exercise = get_exercise(session, user, exercise_id)
    return _form_page(
        request,
        user,
        action=f"/exercises/{exercise.id}",
        values={
            "name": exercise.name,
            "muscle_group": exercise.muscle_group.value,
            "notes": exercise.notes or "",
        },
        errors=[],
    )


@router.post("/{exercise_id}")
async def update(request: Request, session: DbSession, user: RequiredUser, exercise_id: int):
    raw = dict(await request.form())
    action = f"/exercises/{exercise_id}"
    try:
        form = ExerciseForm.model_validate(raw)
    except ValidationError:
        return _form_page(
            request,
            user,
            action=action,
            values=raw,
            errors=["exercises.error.name_required"],
            status_code=400,
        )

    try:
        update_exercise(
            session,
            user,
            exercise_id,
            name=form.name,
            muscle_group=form.muscle_group,
            notes=form.notes,
        )
    except DuplicateExercise:
        return _form_page(
            request,
            user,
            action=action,
            values=raw,
            errors=["exercises.error.duplicate"],
            status_code=409,
        )

    session.commit()
    set_flash(request, "exercises.saved")
    return RedirectResponse(url="/exercises", status_code=303)


@router.post("/{exercise_id}/delete")
def delete(request: Request, session: DbSession, user: RequiredUser, exercise_id: int):
    try:
        delete_exercise(session, user, exercise_id)
    except ExerciseInUse:
        set_flash(request, "exercises.error.in_use", level="error")
        return RedirectResponse(url="/exercises", status_code=303)

    session.commit()
    set_flash(request, "exercises.deleted")
    return RedirectResponse(url="/exercises", status_code=303)
