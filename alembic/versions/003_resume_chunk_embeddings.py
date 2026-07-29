"""resume chunk embeddings with pgvector

Revision ID: 003
Revises: 002
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "resume_chunk_embeddings",
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", sa.String(length=255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("section", sa.String(length=50), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id", "chunk_id"),
    )
    op.create_index(
        "ix_resume_chunk_embeddings_profile_id",
        "resume_chunk_embeddings",
        ["profile_id"],
        unique=False,
    )
    op.execute(
        """
        CREATE INDEX ix_resume_chunk_embeddings_embedding_hnsw
        ON resume_chunk_embeddings
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resume_chunk_embeddings_embedding_hnsw",
        table_name="resume_chunk_embeddings",
    )
    op.drop_index("ix_resume_chunk_embeddings_profile_id", table_name="resume_chunk_embeddings")
    op.drop_table("resume_chunk_embeddings")
