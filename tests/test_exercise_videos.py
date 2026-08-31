from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.exercise_videos import match_video
from app.models import Exercise, ExerciseVideo
from app.services.exercise_videos import extract_youtube_id
from tests.conftest import register


def _add(client: TestClient, name: str, muscle: str = "chest") -> int:
    client.post(
        "/exercises",
        data={"name": name, "muscle_group": muscle, "notes": ""},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        return session.query(Exercise).filter_by(name=name).one().id


# --- units ------------------------------------------------------


def test_extract_youtube_id() -> None:
    cases = {
        "https://www.youtube.com/watch?v=bEv6CCg2BC8": "bEv6CCg2BC8",
        "https://www.youtube.com/watch?v=bEv6CCg2BC8&t=30s": "bEv6CCg2BC8",
        "https://youtu.be/bEv6CCg2BC8": "bEv6CCg2BC8",
        "https://www.youtube.com/embed/bEv6CCg2BC8": "bEv6CCg2BC8",
        "https://www.youtube.com/shorts/bEv6CCg2BC8": "bEv6CCg2BC8",
        "bEv6CCg2BC8": "bEv6CCg2BC8",
    }
    for value, expected in cases.items():
        assert extract_youtube_id(value) == expected

    assert extract_youtube_id("https://example.com/not-a-video") is None
    assert extract_youtube_id("hello") is None


def test_match_video_normalises_equipment_words() -> None:
    assert match_video("Barbell Bench Press").youtube_id == "vcBig73ojpE"
    assert match_video("Back Squat").youtube_id == "bEv6CCg2BC8"
    assert match_video("Machine Overhead Press").youtube_id == "_RlRDWO2jfg"
    assert match_video("Cable Fly") is None


# --- creation + display ---------------------------------------


def test_creating_a_common_lift_seeds_a_video(auth_client: TestClient) -> None:
    exercise_id = _add(auth_client, "Barbell Bench Press")

    with SessionLocal() as session:
        video = session.query(ExerciseVideo).one()
        assert video.youtube_id == "vcBig73ojpE"
        assert video.source == "seed"

    page = auth_client.get(f"/exercises/{exercise_id}")
    assert "youtube-nocookie.com/embed/vcBig73ojpE" in page.text
    assert "Watch on YouTube" in page.text


def test_uncommon_lift_offers_the_nippard_search(auth_client: TestClient) -> None:
    exercise_id = _add(auth_client, "Cable Crossover")

    with SessionLocal() as session:
        assert session.query(ExerciseVideo).count() == 0

    page = auth_client.get(f"/exercises/{exercise_id}")
    assert "youtube.com/@JeffNippard/search?query=Cable%20Crossover" in page.text
    assert 'name="youtube"' in page.text


# --- manual set / clear --------------------------------------


def test_set_and_clear_a_manual_video(auth_client: TestClient) -> None:
    exercise_id = _add(auth_client, "Pec Deck")

    ok = auth_client.post(
        f"/exercises/{exercise_id}/video",
        data={"youtube": "https://youtu.be/dQw4w9WgXcQ"},
        follow_redirects=False,
    )
    assert ok.status_code == 303
    with SessionLocal() as session:
        video = session.query(ExerciseVideo).one()
        assert video.youtube_id == "dQw4w9WgXcQ"
        assert video.source == "manual"

    auth_client.post(f"/exercises/{exercise_id}/video/delete", follow_redirects=False)
    with SessionLocal() as session:
        assert session.query(ExerciseVideo).count() == 0


def test_bad_video_url_is_rejected(auth_client: TestClient) -> None:
    exercise_id = _add(auth_client, "Chest Press Machine")

    resp = auth_client.post(
        f"/exercises/{exercise_id}/video",
        data={"youtube": "just some text"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    with SessionLocal() as session:
        assert session.query(ExerciseVideo).count() == 0


def test_video_routes_are_user_scoped(client: TestClient) -> None:
    register(client, email="a@example.com", display_name="A")
    exercise_id = _add(client, "Incline Bench Press")

    client.cookies.clear()
    register(client, email="b@example.com", display_name="B")

    assert (
        client.post(
            f"/exercises/{exercise_id}/video",
            data={"youtube": "https://youtu.be/dQw4w9WgXcQ"},
            follow_redirects=False,
        ).status_code
        == 404
    )
    assert (
        client.post(f"/exercises/{exercise_id}/video/delete", follow_redirects=False).status_code
        == 404
    )
