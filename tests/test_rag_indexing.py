import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models import Profile
from app.services.rag import DeterministicEmbeddingProvider, chunk_resume
from app.services.rag.indexing import index_profile_chunks
from app.services.rag.job_queries import job_retrieval_queries

FIXTURE_DIR = Path(__file__).parent / "evals" / "fixtures" / "match" / "senior_python_backend"


def _fixture_profile() -> Profile:
    structured_data = json.loads((FIXTURE_DIR / "profile.json").read_text(encoding="utf-8"))
    return Profile(
        id=uuid4(),
        name="Jane Doe",
        headline="Backend Engineer",
        resume_text="Jane Doe resume text",
        structured_data=structured_data,
    )


def _fixture_job():
    job = json.loads((FIXTURE_DIR / "job.json").read_text(encoding="utf-8"))
    return SimpleNamespace(
        title=job["title"],
        company=job["company"],
        description=job["description"],
        location=None,
        raw_metadata={"requirements": ["Python", "FastAPI", "PostgreSQL", "REST APIs"]},
    )


@pytest.mark.asyncio
async def test_index_profile_chunks_writes_rows():
    profile = _fixture_profile()
    embedder = DeterministicEmbeddingProvider()
    session = AsyncMock()
    session.add = MagicMock()

    count = await index_profile_chunks(session, profile, embedder)

    chunks = chunk_resume(profile.structured_data, resume_text=profile.resume_text)
    assert count == len(chunks)
    assert session.add.call_count == len(chunks)


def test_job_retrieval_queries_prefers_requirements():
    queries = job_retrieval_queries(_fixture_job())
    assert queries == ["Python", "FastAPI", "PostgreSQL", "REST APIs"]


def test_job_retrieval_queries_falls_back_to_full_job():
    job = SimpleNamespace(
        title="Engineer",
        company="Acme",
        description="Build APIs",
        location=None,
        raw_metadata={},
    )
    queries = job_retrieval_queries(job)
    assert len(queries) == 1
    assert "Build APIs" in queries[0]
