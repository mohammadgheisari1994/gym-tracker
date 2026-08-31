from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models import Exercise, SetEntry, Workout, WorkoutExercise
from tests.conftest import register


def _make_exercise(client: TestClient, name: str = "Bench") -> int:
    client.post(
        "/exercises",
        data={"name": name, "muscle_group": "chest", "notes": ""},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        return session.query(Exercise).filter_by(name=name).one().id


def _make_workout(client: TestClient) -> int:
    resp = client.post(
        "/workouts",
        data={"performed_on": "2026-08-30", "title": "Push day", "notes": ""},
        follow_redirects=False,
    )
    return int(resp.headers["location"].split("/")[2].split("#")[0])


def _add_entry(client: TestClient, workout_id: int, exercise_id: int) -> int:
    client.post(
        f"/workouts/{workout_id}/exercises",
        data={"exercise_id": str(exercise_id)},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        return (
            session.query(WorkoutExercise)
            .filter_by(workout_id=workout_id, exercise_id=exercise_id)
            .one()
            .id
        )


def _add_set(client: TestClient, entry_id: int, **data) -> None:
    payload = {"weight": "60", "reps": "5", "set_type": "normal", "rpe": ""} | data
    client.post(f"/workout-exercises/{entry_id}/sets", data=payload, follow_redirects=False)


def test_requires_login(client: TestClient) -> None:
    assert client.get("/workouts", follow_redirects=False).status_code == 303


def test_create_workout_redirects_to_detail(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/workouts",
        data={"performed_on": "2026-08-30", "title": "Leg day", "notes": "felt good"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/workouts/")
    detail = auth_client.get(resp.headers["location"])
    assert "Leg day" in detail.text
    assert "felt good" in detail.text


def test_add_exercise_and_sets(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    exercise_id = _make_exercise(auth_client)
    entry_id = _add_entry(auth_client, workout_id, exercise_id)

    _add_set(auth_client, entry_id, weight="60", reps="8", set_type="warmup")
    _add_set(auth_client, entry_id, weight="100", reps="5", set_type="normal")

    with SessionLocal() as session:
        sets = (
            session.query(SetEntry)
            .filter_by(workout_exercise_id=entry_id)
            .order_by(SetEntry.position)
            .all()
        )
        assert [(str(s.weight), s.reps, s.set_type.value) for s in sets] == [
            ("60.00", 8, "warmup"),
            ("100.00", 5, "normal"),
        ]


def test_add_exercise_form_prefills_from_last_set(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    entry_id = _add_entry(auth_client, workout_id, _make_exercise(auth_client))
    _add_set(auth_client, entry_id, weight="82.5", reps="6")

    page = auth_client.get(f"/workouts/{workout_id}")
    assert 'value="82.5"' in page.text
    assert 'value="6"' in page.text


def test_edit_and_delete_set(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    entry_id = _add_entry(auth_client, workout_id, _make_exercise(auth_client))
    _add_set(auth_client, entry_id, weight="60", reps="5")
    with SessionLocal() as session:
        set_id = session.query(SetEntry).one().id

    auth_client.post(
        f"/sets/{set_id}",
        data={"weight": "62.5", "reps": "6", "set_type": "failure", "rpe": "9.5"},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        updated = session.query(SetEntry).one()
        assert str(updated.weight) == "62.50"
        assert updated.reps == 6
        assert updated.set_type.value == "failure"
        assert str(updated.rpe) == "9.5"

    auth_client.post(f"/sets/{set_id}/delete", follow_redirects=False)
    with SessionLocal() as session:
        assert session.query(SetEntry).count() == 0


def test_reorder_sets(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    entry_id = _add_entry(auth_client, workout_id, _make_exercise(auth_client))
    _add_set(auth_client, entry_id, reps="1")
    _add_set(auth_client, entry_id, reps="2")
    with SessionLocal() as session:
        first, second = session.query(SetEntry).order_by(SetEntry.position).all()

    auth_client.post(f"/sets/{second.id}/move", data={"direction": "up"}, follow_redirects=False)
    with SessionLocal() as session:
        ordered = [s.reps for s in session.query(SetEntry).order_by(SetEntry.position).all()]
        assert ordered == [2, 1]


def test_reorder_exercises(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    first = _add_entry(auth_client, workout_id, _make_exercise(auth_client, "A"))
    second = _add_entry(auth_client, workout_id, _make_exercise(auth_client, "B"))

    auth_client.post(
        f"/workout-exercises/{first}/move",
        data={"direction": "down"},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        order = [
            e.id for e in session.query(WorkoutExercise).order_by(WorkoutExercise.position).all()
        ]
        assert order == [second, first]


def test_delete_workout_cascades(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    entry_id = _add_entry(auth_client, workout_id, _make_exercise(auth_client))
    _add_set(auth_client, entry_id)

    auth_client.post(f"/workouts/{workout_id}/delete", follow_redirects=False)
    with SessionLocal() as session:
        assert session.query(Workout).count() == 0
        assert session.query(WorkoutExercise).count() == 0
        assert session.query(SetEntry).count() == 0


def test_cannot_touch_another_users_workout(client: TestClient) -> None:
    register(client, email="a@example.com", display_name="A")
    workout_id = _make_workout(client)
    entry_id = _add_entry(client, workout_id, _make_exercise(client))
    _add_set(client, entry_id)
    with SessionLocal() as session:
        set_id = session.query(SetEntry).one().id

    client.cookies.clear()
    register(client, email="b@example.com", display_name="B")

    assert client.get(f"/workouts/{workout_id}", follow_redirects=False).status_code == 404
    assert client.post(f"/workouts/{workout_id}/delete", follow_redirects=False).status_code == 404
    assert (
        client.post(f"/workout-exercises/{entry_id}/delete", follow_redirects=False).status_code
        == 404
    )
    assert client.post(f"/sets/{set_id}/delete", follow_redirects=False).status_code == 404
    with SessionLocal() as session:
        assert session.query(SetEntry).count() == 1


def test_cannot_add_another_users_exercise(client: TestClient) -> None:
    register(client, email="a@example.com", display_name="A")
    other_exercise = _make_exercise(client, "Secret")

    client.cookies.clear()
    register(client, email="b@example.com", display_name="B")
    workout_id = _make_workout(client)

    resp = client.post(
        f"/workouts/{workout_id}/exercises",
        data={"exercise_id": str(other_exercise)},
        follow_redirects=False,
    )
    assert resp.status_code == 404


def test_exercise_used_in_workout_cannot_be_deleted(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    exercise_id = _make_exercise(auth_client)
    _add_entry(auth_client, workout_id, exercise_id)

    resp = auth_client.post(f"/exercises/{exercise_id}/delete", follow_redirects=False)
    assert resp.status_code == 303
    page = auth_client.get("/exercises")
    assert "used in a workout" in page.text
    with SessionLocal() as session:
        assert session.query(Exercise).count() == 1


def test_profile_settings_round_trip_and_clamp(auth_client: TestClient) -> None:
    auth_client.post(
        "/profile",
        data={
            "display_name": "Test User",
            "preferred_language": "en",
            "weight_unit": "lb",
            "default_rest_seconds": "5000",  # out of range -> clamped to 600
        },
        follow_redirects=False,
    )
    from app.models import User

    with SessionLocal() as session:
        user = session.query(User).one()
        assert user.weight_unit.value == "lb"
        assert user.default_rest_seconds == 600


def test_workout_page_has_rest_timer(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/workouts",
        data={"performed_on": "2026-08-30", "title": "", "notes": ""},
        follow_redirects=False,
    )
    page = auth_client.get(resp.headers["location"])
    assert 'id="rest-timer"' in page.text
    assert 'data-default="120"' in page.text
    assert "js/rest-timer.js" in page.text


_HX = {"HX-Request": "true"}


def test_add_set_via_htmx_returns_only_the_entry_partial(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    entry_id = _add_entry(auth_client, workout_id, _make_exercise(auth_client))

    resp = auth_client.post(
        f"/workout-exercises/{entry_id}/sets",
        data={"weight": "80", "reps": "5", "set_type": "normal", "rpe": ""},
        headers=_HX,
        follow_redirects=False,
    )

    assert resp.status_code == 200
    assert "<!doctype html>" not in resp.text.lower()
    assert f'id="entry-{entry_id}"' in resp.text
    assert 'value="80"' in resp.text  # the new set row
    with SessionLocal() as session:
        assert session.query(SetEntry).count() == 1


def test_delete_set_via_htmx_returns_the_entry_partial(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    entry_id = _add_entry(auth_client, workout_id, _make_exercise(auth_client))
    _add_set(auth_client, entry_id)
    with SessionLocal() as session:
        set_id = session.query(SetEntry).one().id

    resp = auth_client.post(f"/sets/{set_id}/delete", headers=_HX, follow_redirects=False)
    assert resp.status_code == 200
    assert f'id="entry-{entry_id}"' in resp.text
    assert "<!doctype html>" not in resp.text.lower()


def test_add_exercise_via_htmx_returns_all_entries(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    first = _add_entry(auth_client, workout_id, _make_exercise(auth_client, "A"))

    resp = auth_client.post(
        f"/workouts/{workout_id}/exercises",
        data={"exercise_id": str(_make_exercise(auth_client, "B"))},
        headers=_HX,
        follow_redirects=False,
    )

    assert resp.status_code == 200
    assert "<!doctype html>" not in resp.text.lower()
    assert f'id="entry-{first}"' in resp.text
    assert resp.text.count('class="entry"') == 2


def test_non_htmx_set_add_still_redirects(auth_client: TestClient) -> None:
    workout_id = _make_workout(auth_client)
    entry_id = _add_entry(auth_client, workout_id, _make_exercise(auth_client))

    resp = auth_client.post(
        f"/workout-exercises/{entry_id}/sets",
        data={"weight": "80", "reps": "5", "set_type": "normal", "rpe": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303
