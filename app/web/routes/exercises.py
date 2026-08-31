"""The personal exercise catalogue."""

import logging

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.llm import LLMUnavailable
from app.models import MuscleGroup
from app.references import get_many
from app.services.analytics import exercise_progress
from app.services.errors import DuplicateExercise, ExerciseInUse
from app.services.exercises import (
    create_exercise,
    delete_exercise,
    get_exercise,
    list_exercises,
    update_exercise,
)
from app.services.guides import generate_guide, generate_guide_in_background
from app.services.insights import (
    current_exercise_insight,
    refresh_exercise_in_background,
    refresh_exercise_insight,
)
from app.web.chartdata import exercise_chart_data
from app.web.deps import DbSession, LLMProviderDep, RequiredUser, set_flash
from app.web.forms import ExerciseForm
from app.web.templating import render

router = APIRouter(tags=["exercises"], prefix="/exercises")
logger = logging.getLogger(__name__)

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
async def create(
    request: Request,
    session: DbSession,
    user: RequiredUser,
    provider: LLMProviderDep,
    background: BackgroundTasks,
):
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
        exercise = create_exercise(
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
    background.add_task(generate_guide_in_background, exercise.id, provider)
    set_flash(request, "exercises.saved")
    return RedirectResponse(url=f"/exercises/{exercise.id}", status_code=303)


@router.get("/{exercise_id}")
def detail(
    request: Request,
    session: DbSession,
    user: RequiredUser,
    provider: LLMProviderDep,
    exercise_id: int,
):
    exercise = get_exercise(session, user, exercise_id)
    guide = exercise.guide
    sources = get_many(guide.source_slugs) if guide else []
    return render(
        request,
        "exercises/detail.html",
        {
            "exercise": exercise,
            "guide": guide,
            "sources": sources,
            "provider_available": provider.available,
        },
        user=user,
    )


@router.post("/{exercise_id}/guide")
def regenerate_guide(
    request: Request,
    session: DbSession,
    user: RequiredUser,
    provider: LLMProviderDep,
    exercise_id: int,
):
    exercise = get_exercise(session, user, exercise_id)
    if not provider.available:
        set_flash(request, "guide.unavailable", level="error")
        return RedirectResponse(url=f"/exercises/{exercise_id}", status_code=303)

    try:
        generate_guide(session, exercise, provider=provider)
        session.commit()
        set_flash(request, "guide.generated")
    except LLMUnavailable:
        session.rollback()
        set_flash(request, "guide.unavailable", level="error")
    except Exception:
        session.rollback()
        logger.exception("Guide generation failed for exercise %s", exercise_id)
        set_flash(request, "guide.failed", level="error")

    return RedirectResponse(url=f"/exercises/{exercise_id}", status_code=303)


@router.get("/{exercise_id}/progress")
def progress(
    request: Request,
    session: DbSession,
    user: RequiredUser,
    provider: LLMProviderDep,
    background: BackgroundTasks,
    exercise_id: int,
):
    exercise = get_exercise(session, user, exercise_id)
    points = exercise_progress(session, exercise)
    if provider.available and points:
        background.add_task(refresh_exercise_in_background, user.id, exercise.id, provider)
    return render(
        request,
        "exercises/progress.html",
        {
            "exercise": exercise,
            "points": points,
            "chart_data": exercise_chart_data(points),
            "insight": current_exercise_insight(session, user, exercise),
        },
        user=user,
    )


@router.post("/{exercise_id}/insight")
def refresh_exercise_insight_route(
    request: Request,
    session: DbSession,
    user: RequiredUser,
    provider: LLMProviderDep,
    exercise_id: int,
):
    exercise = get_exercise(session, user, exercise_id)
    if not provider.available:
        set_flash(request, "insight.unavailable", level="error")
    else:
        try:
            refresh_exercise_insight(session, user, exercise, provider=provider, force=True)
            session.commit()
            set_flash(request, "insight.refreshed")
        except Exception:
            session.rollback()
            logger.exception("Exercise insight refresh failed for %s", exercise_id)
            set_flash(request, "insight.failed", level="error")
    return RedirectResponse(url=f"/exercises/{exercise_id}/progress", status_code=303)


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
