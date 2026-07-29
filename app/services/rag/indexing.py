"""Persist and refresh profile chunk embeddings."""

from __future__ import annotations

import hashlib

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logging_config import get_logger
from app.models import Profile
from app.models.rag_embeddings import ResumeChunkEmbedding
from app.services.rag.chunking import chunk_resume
from app.services.rag.retrieval import EmbeddingProvider

logger = get_logger(__name__)


def chunk_content_hash(model_name: str, text: str) -> str:
    payload = f"{model_name}\n{text}".encode()
    return hashlib.sha256(payload).hexdigest()


def embedding_model_name(embedder: EmbeddingProvider) -> str:
    return getattr(embedder, "model_name", settings.match_rag_embed_model)


async def count_profile_chunks(db: AsyncSession, profile_id) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(ResumeChunkEmbedding)
        .where(ResumeChunkEmbedding.profile_id == profile_id)
    )
    return int(result.scalar_one())


async def delete_profile_chunks(db: AsyncSession, profile_id) -> None:
    await db.execute(
        delete(ResumeChunkEmbedding).where(ResumeChunkEmbedding.profile_id == profile_id)
    )


async def index_profile_chunks(
    db: AsyncSession,
    profile: Profile,
    embedder: EmbeddingProvider,
) -> int:
    """Chunk a profile, embed, and upsert vectors. Returns indexed chunk count."""
    model_name = embedding_model_name(embedder)
    chunks = chunk_resume(profile.structured_data, resume_text=profile.resume_text)
    await delete_profile_chunks(db, profile.id)

    if not chunks:
        logger.info("RAG index cleared: profile=%s (no chunks)", profile.id)
        return 0

    vectors = embedder.embed([chunk.text for chunk in chunks])
    for chunk, vector in zip(chunks, vectors, strict=True):
        db.add(
            ResumeChunkEmbedding(
                profile_id=profile.id,
                chunk_id=chunk.id,
                text=chunk.text,
                section=chunk.section,
                company=chunk.company,
                title=chunk.title,
                embedding=vector,
                model_name=model_name,
                content_hash=chunk_content_hash(model_name, chunk.text),
            )
        )

    logger.info(
        "RAG index updated: profile=%s chunks=%d model=%s",
        profile.id,
        len(chunks),
        model_name,
    )
    return len(chunks)


async def ensure_profile_indexed(
    db: AsyncSession,
    profile: Profile,
    embedder: EmbeddingProvider,
) -> int:
    """Index profile chunks when missing (e.g. legacy profiles before migration)."""
    if await count_profile_chunks(db, profile.id) > 0:
        return await count_profile_chunks(db, profile.id)
    return await index_profile_chunks(db, profile, embedder)
