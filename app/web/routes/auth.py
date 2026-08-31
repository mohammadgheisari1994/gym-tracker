"""Signup, login, logout, and profile management."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.i18n import LANGUAGE_NAMES, SUPPORTED_LANGUAGES
from app.models import WeightUnit
from app.services.auth import (
    authenticate_user,
    change_password,
    register_user,
    update_profile,
)
from app.services.errors import EmailAlreadyRegistered, InvalidCredentials
from app.web.deps import (
    SESSION_USER_KEY,
    DbSession,
    RequiredUser,
    set_flash,
    set_language_cookie,
)
from app.web.forms import LoginForm, PasswordChangeForm, ProfileForm, SignupForm
from app.web.templating import render

router = APIRouter(tags=["auth"])

_LANGUAGE_CHOICES = [(code, LANGUAGE_NAMES[code]) for code in SUPPORTED_LANGUAGES]


def _describe_errors(exc: ValidationError) -> list[str]:
    """Map pydantic validation failures to translation keys."""
    keys: list[str] = []
    for error in exc.errors():
        field = error["loc"][0] if error["loc"] else ""
        error_type = error["type"]
        if error_type == "value_error" and "match" in error["msg"]:
            keys.append("auth.error.password_mismatch")
        elif error_type in {"string_too_short", "missing"} and "password" in str(field):
            keys.append("auth.error.password_too_short")
        elif error_type in {"string_too_short", "missing"} and field == "display_name":
            keys.append("auth.error.display_name_required")
        elif field == "email":
            keys.append("auth.error.email_invalid")
        else:
            keys.append("auth.error.generic")
    return list(dict.fromkeys(keys))


def _post_login_redirect(preferred_language: str, target: str) -> RedirectResponse:
    response = RedirectResponse(url=target, status_code=303)
    set_language_cookie(response, preferred_language)
    return response


@router.get("/signup")
def signup_form(request: Request):
    if request.session.get(SESSION_USER_KEY):
        return RedirectResponse(url="/dashboard", status_code=303)
    return render(request, "auth/signup.html", {"languages": _LANGUAGE_CHOICES, "errors": []})


@router.post("/signup")
async def signup_submit(request: Request, session: DbSession):
    raw = dict(await request.form())
    try:
        form = SignupForm.model_validate(raw)
    except ValidationError as exc:
        return render(
            request,
            "auth/signup.html",
            {
                "languages": _LANGUAGE_CHOICES,
                "errors": _describe_errors(exc),
                "values": raw,
            },
            status_code=400,
        )

    try:
        user = register_user(
            session,
            email=form.email,
            password=form.password,
            display_name=form.display_name,
            preferred_language=form.preferred_language,
        )
    except EmailAlreadyRegistered:
        return render(
            request,
            "auth/signup.html",
            {
                "languages": _LANGUAGE_CHOICES,
                "errors": ["auth.error.email_taken"],
                "values": raw,
            },
            status_code=409,
        )

    session.commit()
    request.session[SESSION_USER_KEY] = user.id
    return _post_login_redirect(user.preferred_language, "/dashboard")


@router.get("/login")
def login_form(request: Request):
    if request.session.get(SESSION_USER_KEY):
        return RedirectResponse(url="/dashboard", status_code=303)
    return render(request, "auth/login.html", {"errors": []})


@router.post("/login")
async def login_submit(request: Request, session: DbSession):
    raw = dict(await request.form())
    try:
        form = LoginForm.model_validate(raw)
    except ValidationError:
        return render(
            request,
            "auth/login.html",
            {"errors": ["auth.error.invalid_credentials"], "values": raw},
            status_code=400,
        )

    try:
        user = authenticate_user(session, email=form.email, password=form.password)
    except InvalidCredentials:
        return render(
            request,
            "auth/login.html",
            {"errors": ["auth.error.invalid_credentials"], "values": raw},
            status_code=401,
        )

    request.session[SESSION_USER_KEY] = user.id
    return _post_login_redirect(user.preferred_language, "/dashboard")


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


def _profile_page(request: Request, user, errors: list[str], status_code: int = 200):
    return render(
        request,
        "auth/profile.html",
        {
            "languages": _LANGUAGE_CHOICES,
            "weight_units": [unit.value for unit in WeightUnit],
            "errors": errors,
        },
        user=user,
        status_code=status_code,
    )


@router.get("/profile")
def profile_form(request: Request, user: RequiredUser):
    return _profile_page(request, user, errors=[])


@router.post("/profile")
async def profile_submit(request: Request, session: DbSession, user: RequiredUser):
    raw = dict(await request.form())
    try:
        form = ProfileForm.model_validate(raw)
    except ValidationError as exc:
        return _profile_page(request, user, _describe_errors(exc), status_code=400)

    update_profile(
        session,
        user,
        display_name=form.display_name,
        preferred_language=form.preferred_language,
        weight_unit=form.weight_unit,
    )
    session.commit()

    set_flash(request, "auth.profile.saved")
    response = RedirectResponse(url="/profile", status_code=303)
    set_language_cookie(response, user.preferred_language)
    return response


@router.post("/profile/password")
async def profile_change_password(request: Request, session: DbSession, user: RequiredUser):
    raw = dict(await request.form())
    try:
        form = PasswordChangeForm.model_validate(raw)
    except ValidationError as exc:
        return _profile_page(request, user, _describe_errors(exc), status_code=400)

    try:
        change_password(
            session,
            user,
            current_password=form.current_password,
            new_password=form.new_password,
        )
    except InvalidCredentials:
        return _profile_page(request, user, ["auth.error.current_password_wrong"], status_code=400)

    session.commit()
    set_flash(request, "auth.profile.password_changed")
    return RedirectResponse(url="/profile", status_code=303)
