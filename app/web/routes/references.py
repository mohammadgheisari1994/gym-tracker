"""The public references and attributions page."""

from itertools import groupby

from fastapi import APIRouter, Request

from app.references import CATALOG
from app.web.deps import CurrentUser
from app.web.templating import render

router = APIRouter(tags=["pages"])

_KIND_ORDER = ("position_stand", "paper", "formula", "media")


@router.get("/references")
def references(request: Request, user: CurrentUser):
    ordered = sorted(CATALOG, key=lambda ref: (_KIND_ORDER.index(ref.kind), ref.year))
    groups = [(kind, list(items)) for kind, items in groupby(ordered, key=lambda ref: ref.kind)]
    return render(request, "references.html", {"groups": groups}, user=user)
