"""Data export endpoints."""

import csv
import io
import json
from datetime import date

from fastapi import APIRouter
from fastapi.responses import Response

from app.services.export import CSV_COLUMNS, full_export, workout_rows
from app.web.deps import DbSession, RequiredUser

router = APIRouter(tags=["export"], prefix="/export")


def _download_name(extension: str) -> str:
    return f"gym-tracker-workouts-{date.today().isoformat()}.{extension}"


def _attachment(content: str, media_type: str, extension: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{_download_name(extension)}"'},
    )


@router.get("/workouts.csv")
def workouts_csv(session: DbSession, user: RequiredUser) -> Response:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(workout_rows(session, user))
    return _attachment(buffer.getvalue(), "text/csv", "csv")


@router.get("/workouts.json")
def workouts_json(session: DbSession, user: RequiredUser) -> Response:
    payload = json.dumps(full_export(session, user), ensure_ascii=False, indent=2)
    return _attachment(payload, "application/json", "json")
