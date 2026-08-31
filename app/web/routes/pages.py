"""Server-rendered pages."""

import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import RedirectResponse

from app.i18n import get_translator
from app.services.analytics import overall_stats
from app.services.insights import (
    current_overall_insight,
    refresh_overall_in_background,
    refresh_overall_insight,
)
from app.services.motivation import (
    current_quote,
    fallback_index,
    refresh_quote_in_background,
)
from app.web.chartdata import overall_chart_data
from app.web.deps import (
    CurrentUser,
    DbSession,
    LLMProviderDep,
    RequiredUser,
    get_language,
    set_flash,
)
from app.web.templating import render

router = APIRouter(tags=["pages"])
logger = logging.getLogger(__name__)


@router.get("/")
def index(request: Request, user: CurrentUser):
    return render(request, "index.html", user=user)


@router.get("/dashboard")
def dashboard(
    request: Request,
    session: DbSession,
    user: RequiredUser,
    provider: LLMProviderDep,
    background: BackgroundTasks,
):
    stats = overall_stats(session, user)
    translate = get_translator(get_language(request))
    if provider.available:
        background.add_task(refresh_quote_in_background, user.id, provider)
        if stats.has_data:
            background.add_task(refresh_overall_in_background, user.id, provider)

    quote = current_quote(session, user)
    return render(
        request,
        "dashboard.html",
        {
            "stats": stats,
            "chart_data": overall_chart_data(stats, translate),
            "insight": current_overall_insight(session, user),
            "quote": quote,
            "fallback_quote_index": fallback_index(date.today()),
        },
        user=user,
    )


@router.post("/insights/overall")
def refresh_overall(
    request: Request, session: DbSession, user: RequiredUser, provider: LLMProviderDep
):
    if not provider.available:
        set_flash(request, "insight.unavailable", level="error")
    else:
        try:
            refresh_overall_insight(session, user, provider=provider, force=True)
            session.commit()
            set_flash(request, "insight.refreshed")
        except Exception:
            session.rollback()
            logger.exception("Overall insight refresh failed for user %s", user.id)
            set_flash(request, "insight.failed", level="error")
    return RedirectResponse(url="/dashboard", status_code=303)
