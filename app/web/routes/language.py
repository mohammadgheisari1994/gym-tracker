"""Language selection."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.i18n import normalize_language
from app.web.deps import set_language_cookie

router = APIRouter(tags=["language"])


def _safe_next(target: str) -> str:
    """Only allow same-site, absolute-path redirects."""
    if target.startswith("/") and not target.startswith("//"):
        return target
    return "/"


@router.get("/language/{code}")
def set_language(code: str, next: str = "/") -> RedirectResponse:
    response = RedirectResponse(url=_safe_next(next), status_code=303)
    set_language_cookie(response, normalize_language(code))
    return response
