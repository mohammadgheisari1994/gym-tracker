"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.web.routes import health, language, pages

_STATIC_DIR = Path(__file__).parent / "web" / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    app.include_router(health.router)
    app.include_router(pages.router)
    app.include_router(language.router)

    return app


app = create_app()
