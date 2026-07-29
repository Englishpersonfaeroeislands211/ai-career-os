from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.llm.base import LLMConfigurationError, LLMError


@pytest.mark.asyncio
async def test_llm_configuration_error_returns_422(api_client: httpx.AsyncClient):
    with patch(
        "app.api.jobs.structure_job",
        new=AsyncMock(side_effect=LLMConfigurationError("not configured")),
    ):
        response = await api_client.post(
            "/api/v1/jobs/parse-text",
            json={"text": "x" * 100},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "not configured"


@pytest.mark.asyncio
async def test_llm_error_returns_502(api_client: httpx.AsyncClient):
    with patch(
        "app.api.jobs.structure_job",
        new=AsyncMock(side_effect=LLMError("provider down")),
    ):
        response = await api_client.post(
            "/api/v1/jobs/parse-text",
            json={"text": "x" * 100},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "provider down"
