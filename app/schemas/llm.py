from pydantic import BaseModel, Field, field_validator

from app.schemas.providers import LLMProvider


class ListModelsRequest(BaseModel):
    llm_provider: LLMProvider
    llm_api_key: str | None = Field(default=None, min_length=1)
    llm_base_url: str | None = Field(default=None, max_length=500)
    use_saved_credentials: bool = False

    @field_validator("llm_api_key", "llm_base_url", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class ModelListRead(BaseModel):
    models: list[str]
