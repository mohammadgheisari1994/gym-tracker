import csv
import io
import json
from datetime import date

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models import Exercise, WorkoutExercise
from tests.conftest import register


def _log_one_set(client: TestClient, *, exercise="Bench", weight="80", reps="5") -> None:
    client.post(
        "/exercises",
        data={"name": exercise, "muscle_group": "chest", "notes": "cue"},
        follow_redirects=False,
    )
    resp = client.post(
        "/workouts",
        data={"performed_on": "2026-08-20", "title": "Session", "notes": "n"},
        follow_redirects=False,
    )
    workout_id = int(resp.headers["location"].split("/")[2].split("#")[0])
    with SessionLocal() as session:
        exercise_id = session.query(Exercise).filter_by(name=exercise).one().id
    client.post(
        f"/workouts/{workout_id}/exercises",
        data={"exercise_id": str(exercise_id)},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        entry_id = session.query(WorkoutExercise).one().id
    client.post(
        f"/workout-exercises/{entry_id}/sets",
        data={"weight": weight, "reps": reps, "set_type": "normal", "rpe": "8"},
        follow_redirects=False,
    )


def test_requires_login(client: TestClient) -> None:
    assert client.get("/export/workouts.csv", follow_redirects=False).status_code == 303
    assert client.get("/export/workouts.json", follow_redirects=False).status_code == 303


def test_csv_export(auth_client: TestClient) -> None:
    _log_one_set(auth_client, weight="82.5", reps="6")

    response = auth_client.get("/export/workouts.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert date.today().isoformat() in response.headers["content-disposition"]
    assert response.headers["content-disposition"].endswith('.csv"')

    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 1
    assert rows[0]["exercise"] == "Bench"
    assert rows[0]["muscle_group"] == "chest"
    assert rows[0]["weight"] == "82.5"
    assert rows[0]["reps"] == "6"
    assert rows[0]["set_type"] == "normal"


def test_json_export_structure(auth_client: TestClient) -> None:
    _log_one_set(auth_client)

    response = auth_client.get("/export/workouts.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    data = json.loads(response.text)
    assert data["profile"]["display_name"] == "Test User"
    assert data["exercises"][0]["name"] == "Bench"
    assert data["workouts"][0]["exercises"][0]["sets"][0]["reps"] == 5


def test_export_is_user_scoped(client: TestClient) -> None:
    register(client, email="a@example.com", display_name="Alice")
    _log_one_set(client, exercise="Secret Lift")

    client.cookies.clear()
    register(client, email="b@example.com", display_name="Bob")

    csv_body = client.get("/export/workouts.csv").text
    json_body = client.get("/export/workouts.json").text
    assert "Secret Lift" not in csv_body
    assert "Secret Lift" not in json_body
    assert json.loads(json_body)["workouts"] == []
