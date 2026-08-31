"""LLM-written analytical summaries, cached and refreshed when the data changes.

Prompts are built from the analytics payload; the user never types one.
"""

import hashlib
import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.llm import LLMProvider, get_provider
from app.models import Exercise, Insight, User
from app.services.analytics import exercise_progress, overall_stats

logger = logging.getLogger(__name__)

_OVERALL_SCOPE = "overall"

_OVERALL_SYSTEM = (
    "You are a strength coach reviewing a lifter's recent training data (weekly "
    "volume load, weekly session count, and volume by muscle group). Write 2 to "
    "4 short plain-text sentences: the volume trend, the training frequency, and "
    "any muscle-group imbalance worth noting. Use only the numbers provided; "
    "never invent data. No medical advice, no generic motivational filler."
)

_EXERCISE_SYSTEM = (
    "You are a strength coach reviewing one exercise's history (dates with top "
    "weight, total volume, total reps, and estimated one-rep max). Write 2 to 3 "
    "short plain-text sentences on the strength and volume trend and what it "
    "suggests for the next sessions. Use only the numbers provided; never invent "
    "data. No medical advice."
)


def _signature(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _get(session: Session, user_id: int, scope: str) -> Insight | None:
    return session.scalar(select(Insight).where(Insight.user_id == user_id, Insight.scope == scope))


def _exercise_scope(exercise_id: int) -> str:
    return f"exercise:{exercise_id}"


def _overall_payload(stats) -> dict:
    return {
        "weekly_volume": [[week, float(vol)] for week, vol in stats.weekly_volume[-8:]],
        "weekly_frequency": [[week, n] for week, n in stats.weekly_frequency[-8:]],
        "muscle_volume": [
            [mv.muscle_group.value, float(mv.volume)] for mv in stats.muscle_distribution
        ],
    }


def _exercise_payload(points, weight_unit: str) -> dict:
    return {
        "weight_unit": weight_unit,
        "series": [
            {
                "date": point.on.isoformat(),
                "top_weight": (float(point.top_weight) if point.top_weight is not None else None),
                "volume": float(point.volume),
                "reps": point.reps,
                "estimated_1rm": (float(point.best_e1rm) if point.best_e1rm is not None else None),
            }
            for point in points[-12:]
        ],
    }


# --- reads ---------------------------------------------------------------


def current_overall_insight(session: Session, user: User) -> Insight | None:
    return _get(session, user.id, _OVERALL_SCOPE)


def current_exercise_insight(session: Session, user: User, exercise: Exercise) -> Insight | None:
    return _get(session, user.id, _exercise_scope(exercise.id))


# --- refresh ----------------------------------------------------------


def _refresh(
    session: Session,
    user_id: int,
    scope: str,
    payload: dict,
    system: str,
    provider: LLMProvider,
    force: bool,
) -> Insight | None:
    signature = _signature(payload)
    existing = _get(session, user_id, scope)
    if existing is not None and existing.data_signature == signature and not force:
        return existing
    if not provider.available:
        return existing

    result = provider.complete(
        system=system, prompt=json.dumps(payload, default=str), max_tokens=250
    )
    insight = existing or Insight(user_id=user_id, scope=scope)
    insight.body = result.text
    insight.data_signature = signature
    insight.provider = result.provider
    insight.model = result.model
    session.add(insight)
    return insight


def refresh_overall_insight(
    session: Session,
    user: User,
    *,
    provider: LLMProvider | None = None,
    force: bool = False,
) -> Insight | None:
    stats = overall_stats(session, user)
    if not stats.has_data:
        return None
    return _refresh(
        session,
        user.id,
        _OVERALL_SCOPE,
        _overall_payload(stats),
        _OVERALL_SYSTEM,
        provider or get_provider(),
        force,
    )


def refresh_exercise_insight(
    session: Session,
    user: User,
    exercise: Exercise,
    *,
    provider: LLMProvider | None = None,
    force: bool = False,
) -> Insight | None:
    points = exercise_progress(session, exercise)
    if not points:
        return None
    return _refresh(
        session,
        user.id,
        _exercise_scope(exercise.id),
        _exercise_payload(points, user.weight_unit.value),
        _EXERCISE_SYSTEM,
        provider or get_provider(),
        force,
    )


# --- background wrappers -------------------------------------------


def refresh_overall_in_background(user_id: int, provider: LLMProvider) -> None:
    if not provider.available:
        return
    from app.database import SessionLocal
    from app.services.auth import get_user_by_id

    with SessionLocal() as session:
        user = get_user_by_id(session, user_id)
        if user is None:
            return
        try:
            refresh_overall_insight(session, user, provider=provider)
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Overall insight refresh failed for user %s", user_id)


def refresh_exercise_in_background(user_id: int, exercise_id: int, provider: LLMProvider) -> None:
    if not provider.available:
        return
    from app.database import SessionLocal
    from app.services.auth import get_user_by_id

    with SessionLocal() as session:
        user = get_user_by_id(session, user_id)
        exercise = session.get(Exercise, exercise_id)
        if user is None or exercise is None or exercise.user_id != user_id:
            return
        try:
            refresh_exercise_insight(session, user, exercise, provider=provider)
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Exercise insight refresh failed for exercise %s", exercise_id)
