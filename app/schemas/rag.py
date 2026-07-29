"""Schemas for retrieval-augmented match analysis."""

from typing import Literal

from pydantic import BaseModel, Field

ResumeChunkSection = Literal[
    "headline",
    "skill",
    "experience",
    "education",
    "project",
    "resume_text",
]


class ResumeChunk(BaseModel):
    """One citeable unit of resume content for embedding and retrieval."""

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    section: ResumeChunkSection
    company: str | None = None
    title: str | None = None


class ScoredChunk(BaseModel):
    """A resume chunk ranked by retrieval relevance."""

    chunk: ResumeChunk
    score: float
