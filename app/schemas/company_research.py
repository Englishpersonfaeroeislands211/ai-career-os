from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

MAX_RESEARCH_QUERIES = 3
MAX_SEARCH_RESULTS_PER_QUERY = 5
MAX_AGENT_STEPS = 5
MAX_AGENT_SEARCHES = 5


class SearchResult(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2048)
    snippet: str = Field(min_length=1, max_length=2000)


class ResearchPlan(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=MAX_RESEARCH_QUERIES)


class ResearchAgentStep(BaseModel):
    """One step in the bounded company research agent loop."""

    action: Literal["search", "synthesize"]
    query: str | None = Field(default=None, max_length=120)
    rationale: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_action_fields(self) -> Self:
        if self.action == "search" and not (self.query and self.query.strip()):
            raise ValueError("query is required when action is search")
        if self.action == "synthesize":
            self.query = None
        return self


class CompanyBriefContent(BaseModel):
    """LLM-synthesized brief — sources and timestamp are attached in code."""

    company: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1, max_length=2000)
    culture_signals: list[str] = Field(default_factory=list)
    recent_news: list[str] = Field(default_factory=list)
    interview_signals: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)


class CompanyBrief(CompanyBriefContent):
    sources: list[SearchResult] = Field(default_factory=list)
    researched_at: datetime
