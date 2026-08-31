"""Server-rendered pages."""

from fastapi import APIRouter, Request

from app.web.templating import render

router = APIRouter(tags=["pages"])


@router.get("/")
def index(request: Request):
    return render(request, "index.html")
