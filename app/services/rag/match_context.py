"""Build RAG-augmented resume context for match analysis."""

from __future__ import annotations

from pydantic import ValidationError

from app.models import Profile
from app.schemas.rag import ScoredChunk
from app.schemas.resume_extraction import ResumeExtraction
from app.services.rag.chunking import chunk_resume
from app.services.rag.retrieval import EmbeddingProvider, retrieve_chunks


def retrieve_for_match(
    profile: Profile,
    query: str,
    embedder: EmbeddingProvider,
    *,
    top_k: int,
) -> list[ScoredChunk]:
    """Chunk the profile and rank pieces against the job query."""
    chunks = chunk_resume(profile.structured_data, resume_text=profile.resume_text)
    return retrieve_chunks(query, chunks, embedder, top_k=top_k)


def format_rag_resume_section(profile: Profile, scored: list[ScoredChunk]) -> str:
    """Format retrieved chunks plus a short resume summary for the LLM."""
    lines = [
        "Retrieved resume evidence (most relevant to this job):",
        "",
    ]
    for item in scored:
        lines.append(f"[id: {item.chunk.id}] {item.chunk.text}")

    summary = _format_resume_summary(profile)
    if summary:
        lines.extend(["", "Resume summary:", summary])

    return "\n".join(lines)


def _format_resume_summary(profile: Profile) -> str:
    if not profile.structured_data:
        text = (profile.resume_text or "").strip()
        return text[:500] if text else ""

    try:
        extraction = ResumeExtraction.model_validate(profile.structured_data)
    except ValidationError:
        return ""

    parts: list[str] = []
    if extraction.name:
        parts.append(f"Name: {extraction.name}")
    if extraction.headline:
        parts.append(f"Headline: {extraction.headline}")
    if extraction.skills:
        parts.append(f"Skills: {', '.join(extraction.skills)}")
    return "\n".join(parts)
