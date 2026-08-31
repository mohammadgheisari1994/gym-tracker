"""Liveness and readiness endpoint."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database import check_database

router = APIRouter(tags=["system"])


@router.get("/healthz")
def healthz() -> JSONResponse:
    database_ok = check_database()
    payload = {"status": "ok" if database_ok else "degraded", "database": database_ok}
    return JSONResponse(payload, status_code=200 if database_ok else 503)
