import httpx
import pytest


@pytest.mark.asyncio
async def test_update_settings_without_api_key_returns_400(api_client: httpx.AsyncClient):
    response = await api_client.put(
        "/api/v1/settings",
        json={"llm_provider": "openai", "llm_model": "gpt-4o-mini"},
    )

    assert response.status_code == 400
    assert "API key required" in response.json()["detail"]
