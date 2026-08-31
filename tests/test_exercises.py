from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models import Exercise
from tests.conftest import register

ADD = {"name": "Back Squat", "muscle_group": "quadriceps", "notes": "high bar"}


def test_requires_login(client: TestClient) -> None:
    response = client.get("/exercises", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_create_and_list(auth_client: TestClient) -> None:
    created = auth_client.post("/exercises", data=ADD, follow_redirects=False)
    assert created.status_code == 303

    page = auth_client.get("/exercises")
    assert "Back Squat" in page.text
    assert "Quadriceps" in page.text

    with SessionLocal() as session:
        exercise = session.query(Exercise).one()
        assert exercise.name == "Back Squat"
        assert exercise.notes == "high bar"


def test_duplicate_name_is_rejected_case_insensitively(auth_client: TestClient) -> None:
    auth_client.post("/exercises", data=ADD, follow_redirects=False)
    dupe = auth_client.post(
        "/exercises",
        data={"name": "  back squat ", "muscle_group": "other", "notes": ""},
        follow_redirects=False,
    )

    assert dupe.status_code == 409
    assert "already have an exercise" in dupe.text
    with SessionLocal() as session:
        assert session.query(Exercise).count() == 1


def test_name_is_required(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/exercises",
        data={"name": "", "muscle_group": "other", "notes": ""},
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_edit_updates_fields(auth_client: TestClient) -> None:
    auth_client.post("/exercises", data=ADD, follow_redirects=False)
    with SessionLocal() as session:
        exercise_id = session.query(Exercise).one().id

    updated = auth_client.post(
        f"/exercises/{exercise_id}",
        data={"name": "Front Squat", "muscle_group": "core", "notes": ""},
        follow_redirects=False,
    )
    assert updated.status_code == 303

    with SessionLocal() as session:
        exercise = session.query(Exercise).one()
        assert exercise.name == "Front Squat"
        assert exercise.muscle_group.value == "core"
        assert exercise.notes is None


def test_delete_removes_exercise(auth_client: TestClient) -> None:
    auth_client.post("/exercises", data=ADD, follow_redirects=False)
    with SessionLocal() as session:
        exercise_id = session.query(Exercise).one().id

    deleted = auth_client.post(f"/exercises/{exercise_id}/delete", follow_redirects=False)
    assert deleted.status_code == 303
    with SessionLocal() as session:
        assert session.query(Exercise).count() == 0


def test_users_are_isolated(client: TestClient) -> None:
    register(client, email="alice@example.com", display_name="Alice")
    client.post("/exercises", data=ADD, follow_redirects=False)
    with SessionLocal() as session:
        alice_exercise_id = session.query(Exercise).one().id

    client.cookies.clear()
    register(client, email="bob@example.com", display_name="Bob")

    assert "Back Squat" not in client.get("/exercises").text
    assert client.get(f"/exercises/{alice_exercise_id}/edit").status_code == 404
    assert (
        client.post(f"/exercises/{alice_exercise_id}", data=ADD, follow_redirects=False).status_code
        == 404
    )
    assert (
        client.post(f"/exercises/{alice_exercise_id}/delete", follow_redirects=False).status_code
        == 404
    )

    with SessionLocal() as session:
        assert session.query(Exercise).count() == 1
