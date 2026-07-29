import httpx
import pytest
from httpx import ASGITransport

from app.logging_config import REQUEST_ID_HEADER
from app.main import app


@pytest.mark.asyncio
async def test_response_includes_request_id_header():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert REQUEST_ID_HEADER in response.headers
    assert len(response.headers[REQUEST_ID_HEADER]) > 0


@pytest.mark.asyncio
async def test_client_request_id_is_echoed():
    transport = ASGITransport(app=app)
    custom_id = "test-request-id-abc123"
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health", headers={REQUEST_ID_HEADER: custom_id})

    assert response.headers[REQUEST_ID_HEADER] == custom_id
