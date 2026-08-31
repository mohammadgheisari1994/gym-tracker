"""Server-rendered pages."""

from fastapi import APIRouter, Request

from app.web.deps import CurrentUser, RequiredUser
from app.web.templating import render

router = APIRouter(tags=["pages"])


@router.get("/")
def index(request: Request, user: CurrentUser):
    return render(request, "index.html", user=user)


@router.get("/dashboard")
def dashboard(request: Request, user: RequiredUser):
    return render(request, "dashboard.html", user=user)
