from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.providers import DEFAULT_BASE_URLS, OPENAI_COMPATIBLE_PROVIDERS, LLMProvider
from app.services.llm.base import LLMClient, LLMConfigurationError
from app.services.llm.openai_compatible import (
    OpenAICompatibleClient,
    build_openai_compatible_config,
)
from app.services.settings_service import EffectiveLLMSettings, get_effective_llm_settings

_UNSUPPORTED_PROVIDERS: dict[LLMProvider, str] = {
    "anthropic": "Anthropic structured output is not implemented yet.",
    "google": "Google Gemini structured output is not implemented yet.",
}


def create_llm_client(settings: EffectiveLLMSettings) -> LLMClient:
    if settings.provider in OPENAI_COMPATIBLE_PROVIDERS:
        config = build_openai_compatible_config(
            model=settings.model,
            base_url=settings.base_url,
            api_key=settings.api_key,
            default_base_url=DEFAULT_BASE_URLS.get(settings.provider),
        )
        return OpenAICompatibleClient(config)

    message = _UNSUPPORTED_PROVIDERS.get(
        settings.provider,
        f"Provider {settings.provider!r} is not supported yet.",
    )
    raise LLMConfigurationError(message)


async def get_llm_client(db: AsyncSession) -> LLMClient:
    settings = await get_effective_llm_settings(db)
    if settings is None:
        raise LLMConfigurationError(
            "AI provider is not configured. Complete onboarding or update Settings."
        )
    return create_llm_client(settings)
