"""Server-rendered pages."""

from fastapi import APIRouter, Request

from app.i18n import get_translator
from app.services.analytics import overall_stats
from app.web.chartdata import overall_chart_data
from app.web.deps import CurrentUser, DbSession, RequiredUser, get_language
from app.web.templating import render

router = APIRouter(tags=["pages"])


@router.get("/")
def index(request: Request, user: CurrentUser):
    return render(request, "index.html", user=user)


@router.get("/dashboard")
def dashboard(request: Request, session: DbSession, user: RequiredUser):
    stats = overall_stats(session, user)
    translate = get_translator(get_language(request))
    return render(
        request,
        "dashboard.html",
        {"stats": stats, "chart_data": overall_chart_data(stats, translate)},
        user=user,
    )
