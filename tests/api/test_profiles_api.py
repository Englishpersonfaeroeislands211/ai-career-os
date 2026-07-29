from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest


@pytest.mark.asyncio
async def test_create_profile_returns_read_model(api_client: httpx.AsyncClient):
    from unittest.mock import AsyncMock, MagicMock

    from app.db.session import get_db
    from app.main import app
    from app.models import Profile

    profile_id = uuid4()
    now = datetime.now(UTC)

    session = AsyncMock()

    async def refresh_side_effect(obj):
        if isinstance(obj, Profile):
            obj.id = profile_id
            obj.created_at = now
            obj.updated_at = now

    session.refresh = AsyncMock(side_effect=refresh_side_effect)
    session.commit = AsyncMock()
    session.add = MagicMock()

    async def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    try:
        response = await api_client.post(
            "/api/v1/profiles",
            json={
                "name": "Jane Doe",
                "headline": "Engineer",
                "resume_text": "Jane Doe resume text",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Jane Doe"
    assert body["id"] == str(profile_id)
