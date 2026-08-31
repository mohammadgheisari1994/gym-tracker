"""The daily motivational line: consistency signal + an LLM sentence or two.

Falls back to a rotating static line when no provider is configured.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.llm import LLMProvider, get_provider
from app.models import MotivationalQuote, User, Workout

logger = logging.getLogger(__name__)

# Rotating fallbacks, keyed by index; the i18n catalogue holds the text.
FALLBACK_COUNT = 4

_SYSTEM = (
    "You write one short, warm, specific line of encouragement for a weightlifter "
    "based on their recent training consistency data. One or two sentences, plain "
    "text. Reflect what the numbers show — a streak, a return after a gap, a "
    "strong week, or a quiet stretch. No emoji, no hashtags, no clichés like 'no "
    "pain no gain', no medical claims."
)


@dataclass(frozen=True)
class Consistency:
    workouts_last_7_days: int
    workouts_last_30_days: int
    days_since_last_workout: int | None
    week_streak: int


def _week_streak(dates: list[date], today: date) -> int:
    """Consecutive weeks with a workout, ending at the most recent such week."""
    if not dates:
        return 0
    weeks = sorted({d - timedelta(days=d.weekday()) for d in dates}, reverse=True)
    streak = 1
    for earlier, later in zip(weeks[1:], weeks, strict=False):
        if later - earlier == timedelta(days=7):
            streak += 1
        else:
            break
    return streak


def consistency(session: Session, user: User) -> Consistency:
    today = date.today()
    rows = list(session.scalars(select(Workout.performed_on).where(Workout.user_id == user.id)))
    last_7 = sum(1 for d in rows if (today - d).days < 7)
    last_30 = sum(1 for d in rows if (today - d).days < 30)
    since_last = (today - max(rows)).days if rows else None
    return Consistency(last_7, last_30, since_last, _week_streak(rows, today))


def fallback_index(day: date) -> int:
    return day.toordinal() % FALLBACK_COUNT


def current_quote(session: Session, user: User) -> MotivationalQuote | None:
    return session.scalar(select(MotivationalQuote).where(MotivationalQuote.user_id == user.id))


def refresh_quote(
    session: Session,
    user: User,
    *,
    provider: LLMProvider | None = None,
    force: bool = False,
) -> MotivationalQuote | None:
    provider = provider or get_provider()
    today = date.today()
    quote = current_quote(session, user)
    if quote is not None and quote.for_date == today and not force:
        return quote
    if not provider.available:
        return quote

    signal = consistency(session, user)
    result = provider.complete(system=_SYSTEM, prompt=json.dumps(asdict(signal)), max_tokens=120)
    quote = quote or MotivationalQuote(user_id=user.id)
    quote.body = result.text
    quote.for_date = today
    quote.provider = result.provider
    quote.model = result.model
    session.add(quote)
    return quote


def refresh_quote_in_background(user_id: int, provider: LLMProvider) -> None:
    if not provider.available:
        return
    from app.database import SessionLocal
    from app.services.auth import get_user_by_id

    with SessionLocal() as session:
        user = get_user_by_id(session, user_id)
        if user is None:
            return
        try:
            refresh_quote(session, user, provider=provider)
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Quote refresh failed for user %s", user_id)
