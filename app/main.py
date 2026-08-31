"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.web.routes import auth, exercises, health, language, pages, references

_STATIC_DIR = Path(__file__).parent / "web" / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.session_cookie,
        https_only=settings.session_https_only,
        same_site="lax",
    )

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    app.include_router(health.router)
    app.include_router(pages.router)
    app.include_router(language.router)
    app.include_router(auth.router)
    app.include_router(references.router)
    app.include_router(exercises.router)

    return app


app = create_app()
