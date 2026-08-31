from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models import MotivationalQuote, User, Workout
from app.services.motivation import _week_streak, consistency
from tests.conftest import FakeLLM, register


def _new_user(session, email="m@example.com") -> User:
    user = User(email=email, password_hash="x", display_name="M", preferred_language="en")
    session.add(user)
    session.flush()
    return user


# --- consistency units ------------------------------------------


def test_week_streak_counts_consecutive_weeks() -> None:
    today = date(2026, 8, 31)  # a Monday
    dates = [today - timedelta(days=7 * n) for n in range(4)]
    assert _week_streak(dates, today) == 4

    dates_with_gap = [today, today - timedelta(days=7), today - timedelta(days=28)]
    assert _week_streak(dates_with_gap, today) == 2

    assert _week_streak([], today) == 0


def test_consistency_snapshot() -> None:
    with SessionLocal() as session:
        user = _new_user(session)
        today = date.today()
        session.add_all(
            [
                Workout(user_id=user.id, performed_on=today - timedelta(days=1)),
                Workout(user_id=user.id, performed_on=today - timedelta(days=3)),
                Workout(user_id=user.id, performed_on=today - timedelta(days=20)),
            ]
        )
        session.commit()

        signal = consistency(session, user)

    assert signal.workouts_last_7_days == 2
    assert signal.workouts_last_30_days == 3
    assert signal.days_since_last_workout == 1


# --- dashboard integration --------------------------------------


def test_fallback_line_shows_without_a_provider(auth_client: TestClient) -> None:
    page = auth_client.get("/dashboard")

    assert 'class="motivation"' in page.text
    assert "for you, from your recent training" not in page.text  # not the AI note
    with SessionLocal() as session:
        assert session.query(MotivationalQuote).count() == 0


def test_dashboard_generates_and_shows_a_quote(fake_llm: FakeLLM, auth_client: TestClient) -> None:
    fake_llm.text = "Three weeks running now — that rhythm is where the real gains hide."
    auth_client.get("/dashboard")

    with SessionLocal() as session:
        quote = session.query(MotivationalQuote).one()
        assert quote.for_date == date.today()

    page = auth_client.get("/dashboard")
    assert "that rhythm is where the real gains hide" in page.text
    assert "for you, from your recent training" in page.text


def test_quote_is_generated_once_per_day(fake_llm: FakeLLM, auth_client: TestClient) -> None:
    auth_client.get("/dashboard")
    calls = len(fake_llm.calls)
    assert calls >= 1

    auth_client.get("/dashboard")
    assert len(fake_llm.calls) == calls  # same day -> no new call

    with SessionLocal() as session:
        quote = session.query(MotivationalQuote).one()
        quote.for_date = date.today() - timedelta(days=1)
        session.commit()

    auth_client.get("/dashboard")
    assert len(fake_llm.calls) > calls  # stale date -> refresh


def test_quotes_are_user_scoped(fake_llm: FakeLLM, client: TestClient) -> None:
    register(client, email="a@example.com", display_name="A")
    client.get("/dashboard")

    client.cookies.clear()
    register(client, email="b@example.com", display_name="B")
    client.get("/dashboard")

    with SessionLocal() as session:
        assert session.query(MotivationalQuote).count() == 2
