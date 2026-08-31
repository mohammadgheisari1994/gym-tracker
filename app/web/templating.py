"""Jinja2 template rendering with i18n context pre-populated."""

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from app.i18n import LANGUAGE_NAMES, SUPPORTED_LANGUAGES, get_translator, is_rtl
from app.web.deps import get_language

_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def render(request: Request, name: str, context: dict[str, Any] | None = None) -> Response:
    """Render ``name`` with language, direction, and a ``t()`` helper in scope."""
    language = get_language(request)
    full_context: dict[str, Any] = {
        "lang": language,
        "rtl": is_rtl(language),
        "t": get_translator(language),
        "supported_languages": SUPPORTED_LANGUAGES,
        "language_names": LANGUAGE_NAMES,
        "current_path": request.url.path,
    }
    full_context.update(context or {})
    return templates.TemplateResponse(request, name, full_context)
