from dataclasses import dataclass
from typing import Literal

LLMProvider = Literal[
    "openai",
    "anthropic",
    "google",
    "groq",
    "mistral",
    "together",
    "azure_openai",
    "nvidia",
    "local",
]

LocalPreset = Literal["ollama", "lmstudio", "custom"]

ProviderCategory = Literal["cloud", "local"]

# Legacy provider ids — normalized to "local" on read
LEGACY_LOCAL_PROVIDERS = frozenset({"ollama", "lmstudio"})


@dataclass(frozen=True)
class LocalPresetMeta:
    label: str
    default_model: str
    default_base_url: str


@dataclass(frozen=True)
class ProviderMeta:
    label: str
    description: str
    category: ProviderCategory
    default_model: str
    default_base_url: str | None
    requires_api_key: bool
    show_base_url: bool


LOCAL_PRESETS: dict[LocalPreset, LocalPresetMeta] = {
    "ollama": LocalPresetMeta(
        label="Ollama",
        default_model="llama3.2",
        default_base_url="http://127.0.0.1:11434/v1",
    ),
    "lmstudio": LocalPresetMeta(
        label="LM Studio",
        default_model="local-model",
        default_base_url="http://127.0.0.1:1234/v1",
    ),
    "custom": LocalPresetMeta(
        label="Custom",
        default_model="local-model",
        default_base_url="http://127.0.0.1:11434/v1",
    ),
}


PROVIDER_REGISTRY: dict[LLMProvider, ProviderMeta] = {
    "openai": ProviderMeta(
        label="OpenAI",
        description="GPT-4o mini — strong structured outputs",
        category="cloud",
        default_model="gpt-4o-mini",
        default_base_url=None,
        requires_api_key=True,
        show_base_url=False,
    ),
    "anthropic": ProviderMeta(
        label="Anthropic",
        description="Claude Haiku — efficient reasoning",
        category="cloud",
        default_model="claude-haiku-4-5",
        default_base_url=None,
        requires_api_key=True,
        show_base_url=False,
    ),
    "google": ProviderMeta(
        label="Google Gemini",
        description="Gemini Flash — fast multimodal models",
        category="cloud",
        default_model="gemini-2.0-flash",
        default_base_url=None,
        requires_api_key=True,
        show_base_url=False,
    ),
    "groq": ProviderMeta(
        label="Groq",
        description="Ultra-fast inference — OpenAI-compatible API",
        category="cloud",
        default_model="llama-3.3-70b-versatile",
        default_base_url="https://api.groq.com/openai/v1",
        requires_api_key=True,
        show_base_url=True,
    ),
    "mistral": ProviderMeta(
        label="Mistral",
        description="Mistral Small — European frontier models",
        category="cloud",
        default_model="mistral-small-latest",
        default_base_url="https://api.mistral.ai/v1",
        requires_api_key=True,
        show_base_url=True,
    ),
    "together": ProviderMeta(
        label="Together AI",
        description="Open-source models at scale",
        category="cloud",
        default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        default_base_url="https://api.together.xyz/v1",
        requires_api_key=True,
        show_base_url=True,
    ),
    "azure_openai": ProviderMeta(
        label="Azure OpenAI",
        description="Enterprise OpenAI deployments",
        category="cloud",
        default_model="gpt-4o-mini",
        default_base_url=None,
        requires_api_key=True,
        show_base_url=True,
    ),
    "nvidia": ProviderMeta(
        label="NVIDIA NIM",
        description="Hosted models via build.nvidia.com — Nemotron, Llama, Qwen, and more",
        category="cloud",
        default_model="nvidia/llama-3.3-nemotron-super-49b-v1.5",
        default_base_url="https://integrate.api.nvidia.com/v1",
        requires_api_key=True,
        show_base_url=True,
    ),
    "local": ProviderMeta(
        label="Local / Self-hosted",
        description="Ollama, LM Studio, or any OpenAI-compatible server",
        category="local",
        default_model=LOCAL_PRESETS["ollama"].default_model,
        default_base_url=LOCAL_PRESETS["ollama"].default_base_url,
        requires_api_key=False,
        show_base_url=True,
    ),
}

DEFAULT_MODELS: dict[LLMProvider, str] = {k: v.default_model for k, v in PROVIDER_REGISTRY.items()}
DEFAULT_BASE_URLS: dict[LLMProvider, str | None] = {
    k: v.default_base_url for k, v in PROVIDER_REGISTRY.items()
}

LOCAL_PROVIDERS: frozenset[LLMProvider] = frozenset({"local"})

PROVIDER_ENV_KEYS: dict[LLMProvider, str] = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "google": "google_api_key",
    "groq": "groq_api_key",
    "mistral": "mistral_api_key",
    "together": "together_api_key",
    "azure_openai": "azure_openai_api_key",
    "nvidia": "nvidia_api_key",
}

CLOUD_PROVIDERS: list[LLMProvider] = [
    k for k, v in PROVIDER_REGISTRY.items() if v.category == "cloud"
]

OPENAI_COMPATIBLE_PROVIDERS: frozenset[LLMProvider] = frozenset(
    {"openai", "local", "groq", "mistral", "together", "azure_openai", "nvidia"}
)


def normalize_provider(provider: str | None) -> LLMProvider | None:
    if provider is None:
        return None
    if provider in LEGACY_LOCAL_PROVIDERS:
        return "local"
    if provider in PROVIDER_REGISTRY:
        return provider  # type: ignore[return-value]
    return None


def infer_local_preset(base_url: str | None) -> LocalPreset:
    if not base_url:
        return "ollama"
    if "1234" in base_url:
        return "lmstudio"
    if "11434" in base_url:
        return "ollama"
    return "custom"
