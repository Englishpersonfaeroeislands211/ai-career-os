from uuid import UUID

from pydantic import BaseModel, Field


class ScreeningCard(BaseModel):
    """Compressed job representation for Tier 1 LLM screening."""

    job_id: UUID
    title: str
    company: str
    location: str | None = None
    top_requirements: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1, max_length=500)
