"""Jinja2 template rendering with i18n context pre-populated."""

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from app.i18n import LANGUAGE_NAMES, SUPPORTED_LANGUAGES, get_translator, is_rtl
from app.models import User
from app.web.deps import get_language, pop_flash

_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def render(
    request: Request,
    name: str,
    context: dict[str, Any] | None = None,
    *,
    user: User | None = None,
    status_code: int = 200,
) -> Response:
    """Render ``name`` with language, direction, a ``t()`` helper, and the user."""
    language = get_language(request)
    full_context: dict[str, Any] = {
        "lang": language,
        "rtl": is_rtl(language),
        "t": get_translator(language),
        "supported_languages": SUPPORTED_LANGUAGES,
        "language_names": LANGUAGE_NAMES,
        "current_path": request.url.path,
        "current_user": user,
        "flash": pop_flash(request),
    }
    full_context.update(context or {})
    return templates.TemplateResponse(request, name, full_context, status_code=status_code)
