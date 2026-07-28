from typing import Literal

from pydantic import BaseModel, Field

WorkMode = Literal["remote", "hybrid", "on-site", "flexible"]


class JobExtraction(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    company: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    work_mode: WorkMode | None = None
    location: str | None = Field(default=None, max_length=255)
    employment_type: str | None = Field(default=None, max_length=100)
    salary_range: str | None = Field(default=None, max_length=255)
    requirements: list[str] = Field(default_factory=list)
