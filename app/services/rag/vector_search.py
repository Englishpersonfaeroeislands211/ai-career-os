"""Search cached profile embeddings with pgvector."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag_embeddings import ResumeChunkEmbedding
from app.schemas.rag import ResumeChunk, ScoredChunk
from app.services.rag.retrieval import cosine_similarity


def _row_to_chunk(row: ResumeChunkEmbedding) -> ResumeChunk:
    return ResumeChunk(
        id=row.chunk_id,
        text=row.text,
        section=row.section,  # type: ignore[arg-type]
        company=row.company,
        title=row.title,
    )


async def search_profile_chunks(
    db: AsyncSession,
    profile_id: UUID,
    query_vector: list[float],
    *,
    top_k: int,
) -> list[ScoredChunk]:
    """Return the closest resume chunks for a profile using pgvector cosine distance."""
    if top_k <= 0:
        return []

    distance = ResumeChunkEmbedding.embedding.cosine_distance(query_vector)
    stmt = (
        select(ResumeChunkEmbedding)
        .where(ResumeChunkEmbedding.profile_id == profile_id)
        .order_by(distance)
        .limit(top_k)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    scored: list[ScoredChunk] = []
    for row in rows:
        vector = list(row.embedding)
        score = cosine_similarity(query_vector, vector)
        scored.append(ScoredChunk(chunk=_row_to_chunk(row), score=score))

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored
