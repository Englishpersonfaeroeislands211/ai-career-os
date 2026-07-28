from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.job_extraction import JobExtraction
from app.schemas.resume_extraction import ResumeExtraction
from app.schemas.resume_optimization import (
    ApplyResumeSuggestionsRequest as ApplyResumeSuggestionsRequest,
)
from app.schemas.resume_optimization import (
    ResumeOptimizationResult as ResumeOptimizationResult,
)


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    headline: str | None = Field(default=None, max_length=500)
    resume_text: str = Field(min_length=1)
    structured_data: dict | None = None


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    headline: str | None = Field(default=None, max_length=500)
    resume_text: str | None = Field(default=None, min_length=1)
    structured_data: dict | None = None


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    headline: str | None
    resume_text: str
    structured_data: dict | None
    created_at: datetime
    updated_at: datetime


class ResumeParseRead(BaseModel):
    name: str | None = None
    headline: str | None = None
    resume_text: str
    structured_data: ResumeExtraction | None = None


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    company: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    location: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)
    source: str | None = Field(default=None, max_length=100)
    raw_metadata: dict | None = None
    profile_id: UUID | None = None


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    company: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    location: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)
    source: str | None = Field(default=None, max_length=100)
    raw_metadata: dict | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    description: str
    location: str | None
    url: str | None
    source: str | None
    raw_metadata: dict | None
    created_at: datetime
    updated_at: datetime


class JobCreateRead(JobRead):
    """Job create response — includes queued match analysis when profile_id was sent."""

    match_analysis_id: UUID | None = None


class JobParseRequest(BaseModel):
    text: str = Field(min_length=100, max_length=100_000)


class JobParseRead(BaseModel):
    job_text: str
    structured_data: JobExtraction


class MatchAnalysisCreate(BaseModel):
    profile_id: UUID
    job_id: UUID


class MatchAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    job_id: UUID
    status: str
    result: dict | None
    error: str | None
    created_at: datetime
