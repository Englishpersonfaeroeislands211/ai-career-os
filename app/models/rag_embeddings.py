from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.models import Base

if TYPE_CHECKING:
    from app.models import Profile

EMBEDDING_DIMENSIONS = settings.match_rag_embed_dims


class ResumeChunkEmbedding(Base):
    """Cached resume chunk vectors for pgvector similarity search."""

    __tablename__ = "resume_chunk_embeddings"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    chunk_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    text: Mapped[str] = mapped_column(Text())
    section: Mapped[str] = mapped_column(String(50))
    company: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    model_name: Mapped[str] = mapped_column(String(100))
    content_hash: Mapped[str] = mapped_column(String(64))

    profile: Mapped[Profile] = relationship(back_populates="chunk_embeddings")
