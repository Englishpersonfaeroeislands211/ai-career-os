import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logging_config import get_logger
from app.schemas.providers import (
    DEFAULT_BASE_URLS,
    LOCAL_PROVIDERS,
    OPENAI_COMPATIBLE_PROVIDERS,
    PROVIDER_ENV_KEYS,
    PROVIDER_REGISTRY,
    LLMProvider,
)
from app.services.llm.urls import normalize_openai_base_url
from app.services.settings_service import get_settings_row

logger = get_logger(__name__)

OPENAI_DEFAULT_BASE = "https://api.openai.com/v1"
ANTHROPIC_MODELS_URL = "https://api.anthropic.com/v1/models"
GOOGLE_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"

EXCLUDED_MODEL_KEYWORDS = ("embed", "tts", "whisper", "dall-e", "davinci", "babbage")


async def _resolve_credentials(
    db: AsyncSession,
    provider: LLMProvider,
    api_key: str | None,
    base_url: str | None,
    use_saved: bool,
) -> tuple[str | None, str]:
    row = await get_settings_row(db) if use_saved else None

    resolved_key = api_key
    if not resolved_key and use_saved:
        env_attr = PROVIDER_ENV_KEYS.get(provider)
        env_key = getattr(settings, env_attr, None) if env_attr else None
        resolved_key = (row.llm_api_key if row else None) or env_key

    resolved_base = base_url
    if not resolved_base and use_saved and row and row.llm_base_url:
        resolved_base = row.llm_base_url
    if not resolved_base:
        resolved_base = DEFAULT_BASE_URLS[provider]
    if not resolved_base and provider == "openai":
        resolved_base = OPENAI_DEFAULT_BASE

    if provider in OPENAI_COMPATIBLE_PROVIDERS and resolved_base:
        resolved_base = normalize_openai_base_url(resolved_base)

    return resolved_key, resolved_base or ""


def _filter_model_ids(ids: list[str]) -> list[str]:
    filtered = [m for m in ids if not any(k in m.lower() for k in EXCLUDED_MODEL_KEYWORDS)]
    return sorted(set(filtered or ids))


async def _fetch_openai_compatible_models(base_url: str, api_key: str | None) -> list[str]:
    url = f"{base_url.rstrip('/')}/models"
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to {base_url}. Is the server running?",
        ) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Timed out connecting to {base_url}.",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Provider returned {response.status_code}: {response.text[:200]}",
        )

    payload = response.json()
    if isinstance(payload, dict) and payload.get("error"):
        error = payload["error"]
        message = error if isinstance(error, str) else str(error)
        raise HTTPException(status_code=502, detail=f"Provider error: {message}")
    data = payload.get("data", payload)
    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="Unexpected models response format")

    ids: list[str] = []
    for item in data:
        if isinstance(item, dict) and item.get("id"):
            ids.append(str(item["id"]))
        elif isinstance(item, str):
            ids.append(item)

    if not ids:
        raise HTTPException(status_code=502, detail="No models returned by provider")

    return _filter_model_ids(ids)


async def _fetch_anthropic_models(api_key: str) -> list[str]:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(ANTHROPIC_MODELS_URL, headers=headers)
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to Anthropic.") from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=502, detail="Timed out connecting to Anthropic.") from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Anthropic returned {response.status_code}: {response.text[:200]}",
        )

    data = response.json().get("data", [])
    ids = [str(item["id"]) for item in data if isinstance(item, dict) and item.get("id")]
    if not ids:
        raise HTTPException(status_code=502, detail="No models returned by Anthropic")
    return sorted(ids)


async def _fetch_google_models(api_key: str) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(GOOGLE_MODELS_URL, params={"key": api_key})
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to Google.") from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=502, detail="Timed out connecting to Google.") from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Google returned {response.status_code}: {response.text[:200]}",
        )

    models = response.json().get("models", [])
    ids: list[str] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        if name.startswith("models/"):
            name = name.removeprefix("models/")
        if "generateContent" in item.get("supportedGenerationMethods", []):
            ids.append(name)

    if not ids:
        raise HTTPException(status_code=502, detail="No models returned by Google")
    return sorted(ids)


async def list_provider_models(
    db: AsyncSession,
    provider: LLMProvider,
    api_key: str | None,
    base_url: str | None,
    use_saved_credentials: bool,
) -> list[str]:
    meta = PROVIDER_REGISTRY[provider]
    resolved_key, resolved_base = await _resolve_credentials(
        db, provider, api_key, base_url, use_saved_credentials
    )

    if provider not in LOCAL_PROVIDERS and meta.requires_api_key and not resolved_key:
        raise HTTPException(
            status_code=400,
            detail="API key required to list models for this provider.",
        )

    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        if not resolved_base:
            raise HTTPException(status_code=400, detail="Base URL is required for this provider.")
        logger.info("Fetching models from %s at %s", provider, resolved_base)
        return await _fetch_openai_compatible_models(resolved_base, resolved_key)

    if provider == "anthropic":
        assert resolved_key  # validated above
        return await _fetch_anthropic_models(resolved_key)

    if provider == "google":
        assert resolved_key  # validated above
        return await _fetch_google_models(resolved_key)

    raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
