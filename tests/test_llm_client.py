import json

import httpx
import pytest

from app.schemas.resume_extraction import ResumeExtraction
from app.services.llm.base import LLMConfigurationError, Message
from app.services.llm.factory import create_llm_client
from app.services.llm.openai_compatible import (
    OpenAICompatibleClient,
    build_openai_compatible_config,
)
from app.services.settings_service import EffectiveLLMSettings


def _resume_payload() -> dict:
    return {
        "name": "Jane Doe",
        "headline": "Backend Engineer",
        "email": "jane@example.com",
        "phone": None,
        "skills": ["Python", "PostgreSQL"],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Acme",
                "duration": "2020-2024",
                "highlights": ["Built APIs"],
            }
        ],
        "education": [],
        "projects": [],
    }


@pytest.mark.asyncio
async def test_complete_structured_parses_openai_compatible_response():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(_resume_payload()),
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OpenAICompatibleClient(
            build_openai_compatible_config(
                model="qwen/qwen3.5-9b",
                base_url="http://127.0.0.1:1234/v1",
                api_key=None,
            ),
            http_client=http_client,
        )
        result = await client.complete_structured(
            messages=[Message(role="user", content="Extract resume fields.")],
            response_model=ResumeExtraction,
        )

    assert result.name == "Jane Doe"
    assert result.skills == ["Python", "PostgreSQL"]
    assert captured["payload"]["model"] == "qwen/qwen3.5-9b"
    assert captured["payload"]["response_format"]["type"] == "json_schema"


def test_factory_returns_openai_compatible_client_for_local_provider():
    client = create_llm_client(
        EffectiveLLMSettings(
            provider="local",
            model="qwen/qwen3.5-9b",
            api_key=None,
            base_url="http://127.0.0.1:1234/v1",
        )
    )

    assert isinstance(client, OpenAICompatibleClient)


def test_factory_rejects_unimplemented_anthropic_provider():
    with pytest.raises(LLMConfigurationError, match="Anthropic"):
        create_llm_client(
            EffectiveLLMSettings(
                provider="anthropic",
                model="claude-haiku-4-5",
                api_key="sk-test",
                base_url=None,
            )
        )
