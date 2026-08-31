"""Language selection."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.i18n import normalize_language
from app.web.deps import LANGUAGE_COOKIE

router = APIRouter(tags=["language"])

_ONE_YEAR_SECONDS = 60 * 60 * 24 * 365


def _safe_next(target: str) -> str:
    """Only allow same-site, absolute-path redirects."""
    if target.startswith("/") and not target.startswith("//"):
        return target
    return "/"


@router.get("/language/{code}")
def set_language(code: str, next: str = "/") -> RedirectResponse:
    language = normalize_language(code)
    response = RedirectResponse(url=_safe_next(next), status_code=303)
    response.set_cookie(
        LANGUAGE_COOKIE,
        language,
        max_age=_ONE_YEAR_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return response
