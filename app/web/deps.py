"""Shared FastAPI request dependencies."""

from fastapi import Request

from app.config import get_settings
from app.i18n import normalize_language

LANGUAGE_COOKIE = "lang"


def get_language(request: Request) -> str:
    """Resolve the active UI language from the cookie or the configured default."""
    cookie = request.cookies.get(LANGUAGE_COOKIE)
    if cookie is not None:
        return normalize_language(cookie)
    return normalize_language(get_settings().default_language)
