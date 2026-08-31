from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models import Exercise, SetEntry, User, Workout, WorkoutExercise
from app.services.analytics import exercise_progress, overall_stats
from app.services.one_rep_max import epley_one_rep_max
from tests.conftest import register


def _seed(session, user_id: int, *, muscle="chest", name="Bench"):
    exercise = Exercise(user_id=user_id, name=name, muscle_group=muscle, notes=None)
    session.add(exercise)
    session.flush()
    return exercise


def _log(session, workout: Workout, exercise: Exercise, sets: list[tuple]):
    entry = WorkoutExercise(workout_id=workout.id, exercise_id=exercise.id, position=0)
    session.add(entry)
    session.flush()
    for position, (weight, reps) in enumerate(sets):
        session.add(
            SetEntry(
                workout_exercise_id=entry.id,
                position=position,
                weight=weight,
                reps=reps,
                set_type="normal",
                rpe=None,
            )
        )
    session.flush()


# --- Epley -----------------------------------------------------------------


def test_epley_matches_formula() -> None:
    assert epley_one_rep_max(Decimal("100"), 1) == Decimal("103.3")
    assert epley_one_rep_max(Decimal("100"), 5) == Decimal("116.7")
    assert epley_one_rep_max(Decimal("60"), 10) == Decimal("80.0")


def test_epley_none_for_bodyweight() -> None:
    assert epley_one_rep_max(None, 8) is None
    assert epley_one_rep_max(Decimal("50"), 0) is None


# --- per-exercise progress ----------------------------------------------


def test_exercise_progress_points() -> None:
    with SessionLocal() as session:
        user = User(
            email="p@example.com",
            password_hash="x",
            display_name="P",
            preferred_language="en",
        )
        session.add(user)
        session.flush()
        bench = _seed(session, user.id)

        w1 = Workout(user_id=user.id, performed_on=date(2026, 8, 1))
        w2 = Workout(user_id=user.id, performed_on=date(2026, 8, 8))
        session.add_all([w1, w2])
        session.flush()
        _log(session, w1, bench, [(Decimal("60"), 10), (Decimal("80"), 5)])
        _log(session, w2, bench, [(Decimal("85"), 5), (None, 12)])
        session.commit()

        points = exercise_progress(session, bench)

    assert [p.on for p in points] == [date(2026, 8, 1), date(2026, 8, 8)]
    assert points[0].top_weight == Decimal("80")
    assert points[0].volume == Decimal("1000")  # 60*10 + 80*5
    assert points[0].reps == 15
    assert points[1].top_weight == Decimal("85")
    assert points[1].reps == 17  # 5 + 12 (bodyweight reps still count)
    assert points[1].best_e1rm == epley_one_rep_max(Decimal("85"), 5)


# --- overall stats -----------------------------------------------------


def test_overall_stats_buckets_and_isolation() -> None:
    with SessionLocal() as session:
        alice = User(
            email="a@example.com",
            password_hash="x",
            display_name="A",
            preferred_language="en",
        )
        bob = User(
            email="b@example.com",
            password_hash="x",
            display_name="B",
            preferred_language="en",
        )
        session.add_all([alice, bob])
        session.flush()

        bench = _seed(session, alice.id, muscle="chest", name="Bench")
        row = _seed(session, alice.id, muscle="back", name="Row")
        bob_bench = _seed(session, bob.id, name="Bench")

        today = date.today()
        this_week = Workout(user_id=alice.id, performed_on=today)
        last_week = Workout(user_id=alice.id, performed_on=today - timedelta(days=7))
        bob_workout = Workout(user_id=bob.id, performed_on=today)
        session.add_all([this_week, last_week, bob_workout])
        session.flush()

        _log(session, this_week, bench, [(Decimal("100"), 5)])  # 500 chest
        _log(session, this_week, row, [(Decimal("80"), 10)])  # 800 back
        _log(session, last_week, bench, [(Decimal("90"), 5)])  # 450 chest
        _log(session, bob_workout, bob_bench, [(Decimal("999"), 9)])  # not alice's
        session.commit()

        stats = overall_stats(session, alice, weeks=4)

    assert stats.total_workouts == 2
    assert stats.total_volume == Decimal("1750")
    assert stats.weekly_frequency[-1] == (stats.weekly_volume[-1][0], 1)
    assert dict(stats.weekly_volume)[stats.weekly_volume[-1][0]] == Decimal("1300")
    distribution = {mv.muscle_group.value: mv.volume for mv in stats.muscle_distribution}
    assert distribution == {"back": Decimal("800"), "chest": Decimal("950")}
    # sorted by volume desc
    assert stats.muscle_distribution[0].muscle_group.value == "chest"


# --- pages -----------------------------------------------------------


def test_dashboard_empty_state(auth_client: TestClient) -> None:
    page = auth_client.get("/dashboard")
    assert "Log a workout to start" in page.text
    assert "chart-weekly-volume" not in page.text


def test_dashboard_renders_charts_after_logging(auth_client: TestClient) -> None:
    auth_client.post(
        "/exercises",
        data={"name": "Squat", "muscle_group": "quadriceps", "notes": ""},
        follow_redirects=False,
    )
    resp = auth_client.post(
        "/workouts",
        data={"performed_on": date.today().isoformat(), "title": "", "notes": ""},
        follow_redirects=False,
    )
    workout_id = int(resp.headers["location"].split("/")[2].split("#")[0])
    with SessionLocal() as session:
        exercise_id = session.query(Exercise).one().id
    auth_client.post(
        f"/workouts/{workout_id}/exercises",
        data={"exercise_id": str(exercise_id)},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        entry_id = session.query(WorkoutExercise).one().id
    auth_client.post(
        f"/workout-exercises/{entry_id}/sets",
        data={"weight": "100", "reps": "5", "set_type": "normal", "rpe": ""},
        follow_redirects=False,
    )

    page = auth_client.get("/dashboard")
    assert "chart-weekly-volume" in page.text
    assert "dashboard-data" in page.text

    progress = auth_client.get(f"/exercises/{exercise_id}/progress")
    assert "chart-strength" in progress.text
    assert "Estimated 1RM" in progress.text


def test_progress_is_user_scoped(client: TestClient) -> None:
    register(client, email="a@example.com", display_name="A")
    client.post(
        "/exercises",
        data={"name": "Bench", "muscle_group": "chest", "notes": ""},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        exercise_id = session.query(Exercise).one().id

    client.cookies.clear()
    register(client, email="b@example.com", display_name="B")
    assert (
        client.get(f"/exercises/{exercise_id}/progress", follow_redirects=False).status_code == 404
    )
