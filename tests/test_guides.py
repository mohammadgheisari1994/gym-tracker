import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.llm import get_provider
from app.llm.base import LLMProvider, LLMResult
from app.llm.http_provider import HttpChatProvider
from app.main import app
from app.models import Exercise, ExerciseGuide
from app.services.guides import _SYSTEM_PROMPT, GUIDE_SOURCE_SLUGS
from app.web.deps import get_llm_provider
from tests.conftest import register

_GUIDE_TEXT = (
    "Setup: brace your core and set your feet.\n"
    "1. Lower under control.\n"
    "2. Drive back up.\n"
    "Range of motion: full depth without losing a neutral spine."
)


class FakeProvider(LLMProvider):
    name = "fake"

    def __init__(self, text: str = _GUIDE_TEXT) -> None:
        self.text = text
        self.calls: list[str] = []

    @property
    def available(self) -> bool:
        return True

    def complete(self, *, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        self.calls.append(prompt)
        return LLMResult(text=self.text, provider="fake", model="fake-1")


@pytest.fixture
def fake_llm():
    provider = FakeProvider()
    app.dependency_overrides[get_llm_provider] = lambda: provider
    yield provider
    app.dependency_overrides.pop(get_llm_provider, None)


def _add_exercise(client: TestClient, name: str = "Squat") -> int:
    client.post(
        "/exercises",
        data={"name": name, "muscle_group": "quadriceps", "notes": ""},
        follow_redirects=False,
    )
    with SessionLocal() as session:
        return session.query(Exercise).filter_by(name=name).one().id


# --- provider units --------------------------------------------------


def test_default_provider_is_unavailable() -> None:
    assert get_provider().available is False


def test_http_provider_key_requirement() -> None:
    groq = HttpChatProvider(name="groq", base_url="https://x", model="m", requires_key=True)
    assert groq.available is False
    groq_with_key = HttpChatProvider(
        name="groq", base_url="https://x", model="m", api_key="k", requires_key=True
    )
    assert groq_with_key.available is True

    ollama = HttpChatProvider(name="ollama", base_url="http://x/v1", model="m")
    assert ollama.available is True


def test_system_prompt_forbids_named_sources() -> None:
    lowered = _SYSTEM_PROMPT.lower()
    assert "do not name any person, brand" in lowered
    assert "do not copy wording" in lowered


# --- guide generation ----------------------------------------------


def test_creating_exercise_generates_and_shows_guide(
    fake_llm: FakeProvider, auth_client: TestClient
) -> None:
    exercise_id = _add_exercise(auth_client)

    assert fake_llm.calls, "the background task should have called the provider"
    with SessionLocal() as session:
        guide = session.query(ExerciseGuide).one()
        assert guide.provider == "fake"
        assert list(guide.source_slugs) == list(GUIDE_SOURCE_SLUGS)

    page = auth_client.get(f"/exercises/{exercise_id}")
    assert "Drive back up." in page.text
    assert "coaching or medical advice" in page.text
    assert "Further reading" in page.text


def test_no_provider_shows_unavailable(auth_client: TestClient) -> None:
    exercise_id = _add_exercise(auth_client)

    with SessionLocal() as session:
        assert session.query(ExerciseGuide).count() == 0

    page = auth_client.get(f"/exercises/{exercise_id}")
    assert "no LLM provider is configured" in page.text


def test_regenerate_replaces_the_guide(fake_llm: FakeProvider, auth_client: TestClient) -> None:
    exercise_id = _add_exercise(auth_client)

    fake_llm.text = "Setup: new cue.\n1. New step.\nRange of motion: new."
    resp = auth_client.post(f"/exercises/{exercise_id}/guide", follow_redirects=False)
    assert resp.status_code == 303

    with SessionLocal() as session:
        guide = session.query(ExerciseGuide).one()  # still exactly one
        assert "New step." in guide.body


def test_guide_routes_are_user_scoped(fake_llm: FakeProvider, client: TestClient) -> None:
    register(client, email="a@example.com", display_name="A")
    exercise_id = _add_exercise(client, "Secret")

    client.cookies.clear()
    register(client, email="b@example.com", display_name="B")

    assert client.get(f"/exercises/{exercise_id}", follow_redirects=False).status_code == 404
    assert client.post(f"/exercises/{exercise_id}/guide", follow_redirects=False).status_code == 404
