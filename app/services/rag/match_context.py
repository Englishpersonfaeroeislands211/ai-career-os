"""Build RAG-augmented resume context for match analysis."""

from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Job, Profile
from app.schemas.rag import ScoredChunk
from app.schemas.resume_extraction import ResumeExtraction
from app.services.rag.chunking import chunk_resume
from app.services.rag.indexing import ensure_profile_indexed
from app.services.rag.job_queries import job_retrieval_queries
from app.services.rag.retrieval import EmbeddingProvider, retrieve_chunks
from app.services.rag.vector_search import search_profile_chunks


def _merge_scored_chunks(items: list[ScoredChunk]) -> list[ScoredChunk]:
    best: dict[str, ScoredChunk] = {}
    for item in items:
        existing = best.get(item.chunk.id)
        if existing is None or item.score > existing.score:
            best[item.chunk.id] = item
    return sorted(best.values(), key=lambda entry: entry.score, reverse=True)


def _retrieve_in_memory(
    profile: Profile,
    queries: list[str],
    embedder: EmbeddingProvider,
    *,
    per_query_top_k: int,
    total_top_k: int,
) -> list[ScoredChunk]:
    chunks = chunk_resume(profile.structured_data, resume_text=profile.resume_text)
    if not chunks:
        return []

    collected: list[ScoredChunk] = []
    for query in queries:
        collected.extend(retrieve_chunks(query, chunks, embedder, top_k=per_query_top_k))
    return _merge_scored_chunks(collected)[:total_top_k]


async def retrieve_for_match(
    db: AsyncSession | None,
    profile: Profile,
    job: Job,
    embedder: EmbeddingProvider,
    *,
    top_k: int,
) -> list[ScoredChunk]:
    """Retrieve resume evidence for a job using pgvector or an in-memory fallback."""
    queries = job_retrieval_queries(job)
    use_per_requirement = settings.match_rag_per_requirement and len(queries) > 1
    per_query_top_k = settings.match_rag_per_requirement_top_k if use_per_requirement else top_k

    if db is None:
        return _retrieve_in_memory(
            profile,
            queries,
            embedder,
            per_query_top_k=per_query_top_k,
            total_top_k=top_k,
        )

    await ensure_profile_indexed(db, profile, embedder)

    collected: list[ScoredChunk] = []
    query_vectors = embedder.embed(queries)
    for query_vector in query_vectors:
        collected.extend(
            await search_profile_chunks(
                db,
                profile.id,
                query_vector,
                top_k=per_query_top_k,
            )
        )

    return _merge_scored_chunks(collected)[:top_k]


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
