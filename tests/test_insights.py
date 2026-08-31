from datetime import date

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models import Exercise, Insight, WorkoutExercise
from tests.conftest import FakeLLM, register


def _log_workout(client: TestClient, *, weight: str = "100", reps: str = "5") -> int:
    client.post(
        "/exercises",
        data={"name": "Bench", "muscle_group": "chest", "notes": ""},
        follow_redirects=False,
    )
    resp = client.post(
        "/workouts",
        data={"performed_on": date.today().isoformat(), "title": "", "notes": ""},
        follow_redirects=False,
    )
    workout_id = int(resp.headers["location"].split("/")[2].split("#")[0])
    with SessionLocal() as session:
        exercise_id = session.query(Exercise).filter_by(name="Bench").one().id
    client.post(
        f"/workouts/{workout_id}/exercises",
        data={"exercise_id": str(exercise_id)},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        entry_id = session.query(WorkoutExercise).filter_by(workout_id=workout_id).one().id
    client.post(
        f"/workout-exercises/{entry_id}/sets",
        data={"weight": weight, "reps": reps, "set_type": "normal", "rpe": ""},
        follow_redirects=False,
    )
    return exercise_id


def test_no_provider_no_insight(auth_client: TestClient) -> None:
    _log_workout(auth_client)
    page = auth_client.get("/dashboard")

    with SessionLocal() as session:
        assert session.query(Insight).count() == 0
    assert "insight-card" not in page.text


def test_dashboard_generates_overall_insight(fake_llm: FakeLLM, auth_client: TestClient) -> None:
    fake_llm.text = "Volume is trending up and frequency is steady at one session a week."
    _log_workout(auth_client)

    auth_client.get("/dashboard")  # schedules + runs the background refresh

    with SessionLocal() as session:
        insight = session.query(Insight).one()
        assert insight.scope == "overall"
        assert "trending up" in insight.body

    page = auth_client.get("/dashboard")
    assert "trending up" in page.text
    assert "not coaching or medical advice" in page.text


def test_insight_is_cached_until_the_data_changes(
    fake_llm: FakeLLM, auth_client: TestClient
) -> None:
    _log_workout(auth_client)
    auth_client.get("/dashboard")
    first_call_count = len(fake_llm.calls)
    assert first_call_count >= 1

    auth_client.get("/dashboard")  # same data -> no new provider call
    assert len(fake_llm.calls) == first_call_count

    _log_workout(auth_client)  # new set -> signature changes
    auth_client.get("/dashboard")
    assert len(fake_llm.calls) > first_call_count


def test_progress_page_generates_exercise_insight(
    fake_llm: FakeLLM, auth_client: TestClient
) -> None:
    fake_llm.text = "Top weight and estimated 1RM are climbing; keep adding small jumps."
    exercise_id = _log_workout(auth_client)

    auth_client.get(f"/exercises/{exercise_id}/progress")

    with SessionLocal() as session:
        insight = session.query(Insight).filter_by(scope=f"exercise:{exercise_id}").one()
        assert "climbing" in insight.body


def test_manual_overall_refresh(fake_llm: FakeLLM, auth_client: TestClient) -> None:
    _log_workout(auth_client)
    resp = auth_client.post("/insights/overall", follow_redirects=False)
    assert resp.status_code == 303
    with SessionLocal() as session:
        assert session.query(Insight).filter_by(scope="overall").count() == 1


def test_insights_are_user_scoped(fake_llm: FakeLLM, client: TestClient) -> None:
    register(client, email="a@example.com", display_name="A")
    _log_workout(client)
    client.get("/dashboard")

    client.cookies.clear()
    register(client, email="b@example.com", display_name="B")
    page = client.get("/dashboard")
    assert "insight-card" not in page.text
    with SessionLocal() as session:
        assert session.query(Insight).count() == 1
