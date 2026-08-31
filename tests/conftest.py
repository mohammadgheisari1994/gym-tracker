from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.llm.base import LLMProvider, LLMResult
from app.main import app
from app.models import Base
from app.web.deps import get_llm_provider


@pytest.fixture(scope="session", autouse=True)
def _schema() -> None:
    """Ensure the schema exists for the whole test session."""
    Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    """Give every test an empty database."""
    yield
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def register(
    client: TestClient,
    *,
    email: str = "user@example.com",
    display_name: str = "Test User",
    password: str = "barbell123",
) -> None:
    """Sign a user up and leave the client authenticated as them."""
    client.post(
        "/signup",
        data={
            "display_name": display_name,
            "email": email,
            "password": password,
            "password_confirm": password,
            "preferred_language": "en",
        },
        follow_redirects=False,
    )


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """A client already signed in as a default user."""
    register(client)
    return client


class FakeLLM(LLMProvider):
    name = "fake"

    def __init__(self, text: str = "Setup: brace.\n1. Move well.\nRange of motion: full.") -> None:
        self.text = text
        self.calls: list[str] = []

    @property
    def available(self) -> bool:
        return True

    def complete(self, *, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        self.calls.append(prompt)
        return LLMResult(text=self.text, provider="fake", model="fake-1")


@pytest.fixture
def fake_llm() -> Iterator[FakeLLM]:
    provider = FakeLLM()
    app.dependency_overrides[get_llm_provider] = lambda: provider
    yield provider
    app.dependency_overrides.pop(get_llm_provider, None)
