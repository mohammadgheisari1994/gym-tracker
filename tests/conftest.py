from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.main import app
from app.models import Base


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
