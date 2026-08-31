import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import SessionLocal
from app.llm import get_provider
from app.llm.http_provider import HttpChatProvider
from app.models import Exercise, ExerciseGuide
from app.services.guides import _SYSTEM_PROMPT, GUIDE_SOURCE_SLUGS
from tests.conftest import FakeLLM, register


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


@pytest.fixture
def _reset_provider_cache():
    get_settings.cache_clear()
    get_provider.cache_clear()
    yield
    get_settings.cache_clear()
    get_provider.cache_clear()


def test_openai_provider_mode(monkeypatch, _reset_provider_cache) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

    provider = get_provider()
    assert provider.name == "openai"
    assert provider.available is True  # base url + model is enough, key optional


def test_unknown_provider_falls_back_to_null(monkeypatch, _reset_provider_cache) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "banana")
    provider = get_provider()
    assert provider.name == "none"
    assert provider.available is False


def test_system_prompt_forbids_named_sources() -> None:
    lowered = _SYSTEM_PROMPT.lower()
    assert "do not name any person, brand" in lowered
    assert "do not copy wording" in lowered


# --- guide generation ----------------------------------------------


def test_creating_exercise_generates_and_shows_guide(
    fake_llm: FakeLLM, auth_client: TestClient
) -> None:
    exercise_id = _add_exercise(auth_client)

    assert fake_llm.calls, "the background task should have called the provider"
    with SessionLocal() as session:
        guide = session.query(ExerciseGuide).one()
        assert guide.provider == "fake"
        assert list(guide.source_slugs) == list(GUIDE_SOURCE_SLUGS)

    page = auth_client.get(f"/exercises/{exercise_id}")
    assert "Move well." in page.text
    assert "coaching or medical advice" in page.text
    assert "Further reading" in page.text


def test_no_provider_shows_unavailable(auth_client: TestClient) -> None:
    exercise_id = _add_exercise(auth_client)

    with SessionLocal() as session:
        assert session.query(ExerciseGuide).count() == 0

    page = auth_client.get(f"/exercises/{exercise_id}")
    assert "no LLM provider is configured" in page.text


def test_regenerate_replaces_the_guide(fake_llm: FakeLLM, auth_client: TestClient) -> None:
    exercise_id = _add_exercise(auth_client)

    fake_llm.text = "Setup: new cue.\n1. New step.\nRange of motion: new."
    resp = auth_client.post(f"/exercises/{exercise_id}/guide", follow_redirects=False)
    assert resp.status_code == 303

    with SessionLocal() as session:
        guide = session.query(ExerciseGuide).one()  # still exactly one
        assert "New step." in guide.body


def test_guide_routes_are_user_scoped(fake_llm: FakeLLM, client: TestClient) -> None:
    register(client, email="a@example.com", display_name="A")
    exercise_id = _add_exercise(client, "Secret")

    client.cookies.clear()
    register(client, email="b@example.com", display_name="B")

    assert client.get(f"/exercises/{exercise_id}", follow_redirects=False).status_code == 404
    assert client.post(f"/exercises/{exercise_id}/guide", follow_redirects=False).status_code == 404
