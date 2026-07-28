from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class MatchStrength(BaseModel):
    point: float = Field(ge=0, le=10)
    evidence: str = Field(min_length=1)


class MatchGap(BaseModel):
    point: float = Field(ge=0, le=10)
    severity: Literal["low", "medium", "high"]
    evidence: str = Field(min_length=1)


class MatchResult(BaseModel):
    score: float = Field(ge=0, le=100)
    recommendation: Literal["apply", "maybe apply", "do not apply"]
    strengths: list[MatchStrength] = Field(default_factory=list)
    gaps: list[MatchGap] = Field(default_factory=list)
    summary: str = Field(min_length=1)


class JobMatchResult(MatchResult):
    """Per-job match within a batch — includes job_id for mapping results."""

    job_id: UUID


class BatchMatchResult(BaseModel):
    matches: list[JobMatchResult] = Field(min_length=1)


class ScreeningJobMatchResult(BaseModel):
    job_id: UUID
    score: float = Field(ge=0, le=100)
    recommendation: Literal["apply", "maybe apply", "do not apply"]
    reason: str = Field(min_length=1)


class BatchScreeningResult(BaseModel):
    matches: list[ScreeningJobMatchResult] = Field(min_length=1)
