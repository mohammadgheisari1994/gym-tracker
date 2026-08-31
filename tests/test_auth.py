from fastapi.testclient import TestClient
from httpx import Response

from app.database import SessionLocal
from app.models import User
from app.security import verify_password

SIGNUP = {
    "display_name": "Sam Lifter",
    "email": "sam@example.com",
    "password": "barbell123",
    "password_confirm": "barbell123",
    "preferred_language": "en",
}


def _signup(client: TestClient, **overrides: str) -> Response:
    payload = SIGNUP | overrides
    return client.post("/signup", data=payload, follow_redirects=False)


def test_signup_creates_hashed_user_and_session(client: TestClient) -> None:
    response = _signup(client)

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"

    with SessionLocal() as session:
        user = session.query(User).one()
        assert user.email == "sam@example.com"
        assert user.password_hash != "barbell123"
        assert verify_password("barbell123", user.password_hash)

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Sam Lifter" in dashboard.text


def test_signup_rejects_duplicate_email(client: TestClient) -> None:
    _signup(client)
    response = _signup(client, display_name="Impostor")

    assert response.status_code == 409
    assert "already exists" in response.text
    with SessionLocal() as session:
        assert session.query(User).count() == 1


def test_signup_rejects_password_mismatch(client: TestClient) -> None:
    response = _signup(client, password_confirm="different")

    assert response.status_code == 400
    assert "do not match" in response.text
    with SessionLocal() as session:
        assert session.query(User).count() == 0


def test_signup_rejects_short_password(client: TestClient) -> None:
    response = _signup(client, password="short", password_confirm="short")

    assert response.status_code == 400
    assert "at least 8" in response.text


def test_login_with_correct_password_starts_session(client: TestClient) -> None:
    _signup(client)
    client.cookies.clear()

    response = client.post(
        "/login",
        data={"email": "sam@example.com", "password": "barbell123"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert client.get("/dashboard").status_code == 200


def test_login_with_wrong_password_is_rejected(client: TestClient) -> None:
    _signup(client)
    client.cookies.clear()

    response = client.post(
        "/login",
        data={"email": "sam@example.com", "password": "wrong"},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert "incorrect" in response.text


def test_logout_clears_session(client: TestClient) -> None:
    _signup(client)
    client.post("/logout", follow_redirects=False)

    guarded = client.get("/dashboard", follow_redirects=False)
    assert guarded.status_code == 303
    assert guarded.headers["location"] == "/login"


def test_dashboard_requires_login(client: TestClient) -> None:
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_profile_update_changes_language_and_name(client: TestClient) -> None:
    _signup(client)

    response = client.post(
        "/profile",
        data={"display_name": "Samantha", "preferred_language": "fa"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert client.cookies.get("lang") == "fa"
    with SessionLocal() as session:
        user = session.query(User).one()
        assert user.display_name == "Samantha"
        assert user.preferred_language == "fa"

    profile = client.get("/profile")
    assert "نمایه به‌روزرسانی شد." in profile.text  # flashed, now in Persian
    assert 'dir="rtl"' in profile.text

    # Flash is one-shot: gone on the next load.
    assert "نمایه به‌روزرسانی شد." not in client.get("/profile").text


def test_password_change_requires_correct_current_password(client: TestClient) -> None:
    _signup(client)

    wrong = client.post(
        "/profile/password",
        data={
            "current_password": "nope",
            "new_password": "newbarbell1",
            "new_password_confirm": "newbarbell1",
        },
        follow_redirects=False,
    )
    assert wrong.status_code == 400

    ok = client.post(
        "/profile/password",
        data={
            "current_password": "barbell123",
            "new_password": "newbarbell1",
            "new_password_confirm": "newbarbell1",
        },
        follow_redirects=False,
    )
    assert ok.status_code == 303

    client.cookies.clear()
    login = client.post(
        "/login",
        data={"email": "sam@example.com", "password": "newbarbell1"},
        follow_redirects=False,
    )
    assert login.status_code == 303
