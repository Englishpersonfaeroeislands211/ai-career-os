from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "AI Career OS"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://career:career@127.0.0.1:5432/ai_career_os"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Match analysis: retrieve relevant resume chunks before LLM call
    match_rag_enabled: bool = True
    match_rag_top_k: int = 15

    # Optional env fallbacks for LLM (overridden by DB settings when set)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    groq_api_key: str | None = None
    mistral_api_key: str | None = None
    together_api_key: str | None = None
    azure_openai_api_key: str | None = None


settings = Settings()
