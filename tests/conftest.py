"""Shared pytest fixtures for unit and API tests."""

from collections.abc import AsyncGenerator, Callable
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from httpx import ASGITransport

from app.db.session import get_db
from app.main import app


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Minimal async SQLAlchemy session mock."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.get = AsyncMock(return_value=None)
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_db_session_empty_lists(mock_db_session: AsyncMock) -> AsyncMock:
    """Session mock whose ``execute()`` returns empty ORM lists."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    mock_db_session.execute = AsyncMock(return_value=result)
    return mock_db_session


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """LLM client mock with ``generate_structured`` stubbed."""
    client = AsyncMock()
    client.generate_structured = AsyncMock()
    return client


@pytest.fixture
def override_get_db() -> Callable[[AsyncMock], None]:
    """Replace FastAPI ``get_db`` with a provided session mock."""

    def _apply(session: AsyncMock) -> None:
        async def _override() -> AsyncGenerator[AsyncMock, None]:
            yield session

        app.dependency_overrides[get_db] = _override

    yield _apply
    app.dependency_overrides.clear()


@pytest.fixture
async def api_client(
    mock_db_session_empty_lists: AsyncMock,
    override_get_db: Callable[[AsyncMock], None],
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client against the FastAPI app with a mocked database."""
    override_get_db(mock_db_session_empty_lists)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
