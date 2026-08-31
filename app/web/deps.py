"""Shared FastAPI request dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.config import get_settings
from app.database import get_session
from app.i18n import normalize_language
from app.models import User
from app.services.auth import get_user_by_id

LANGUAGE_COOKIE = "lang"
SESSION_USER_KEY = "user_id"
FLASH_SESSION_KEY = "flash"
_LANGUAGE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365

DbSession = Annotated[Session, Depends(get_session)]


def set_flash(request: Request, message_key: str, *, level: str = "success") -> None:
    """Stash a one-shot message shown on the next rendered page."""
    request.session[FLASH_SESSION_KEY] = {"key": message_key, "level": level}


def pop_flash(request: Request) -> dict[str, str] | None:
    return request.session.pop(FLASH_SESSION_KEY, None)


def set_language_cookie(response: Response, language: str) -> None:
    response.set_cookie(
        LANGUAGE_COOKIE,
        language,
        max_age=_LANGUAGE_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )


def get_language(request: Request) -> str:
    """Resolve the active UI language from the cookie or the configured default."""
    cookie = request.cookies.get(LANGUAGE_COOKIE)
    if cookie is not None:
        return normalize_language(cookie)
    return normalize_language(get_settings().default_language)


def get_current_user(request: Request, session: DbSession) -> User | None:
    """Return the signed-in user, or ``None`` for an anonymous visitor."""
    user_id = request.session.get(SESSION_USER_KEY)
    if user_id is None:
        return None
    return get_user_by_id(session, user_id)


CurrentUser = Annotated["User | None", Depends(get_current_user)]


def require_user(user: CurrentUser) -> User:
    """Guard a route: redirect anonymous visitors to the login page."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return user


RequiredUser = Annotated[User, Depends(require_user)]
