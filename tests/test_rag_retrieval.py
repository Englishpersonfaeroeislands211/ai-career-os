import json
from pathlib import Path

from app.services.rag import (
    DeterministicEmbeddingProvider,
    chunk_resume,
    retrieve_chunks,
)

FIXTURE_DIR = Path(__file__).parent / "evals" / "fixtures" / "match" / "senior_python_backend"


def _load_job_query() -> str:
    job = json.loads((FIXTURE_DIR / "job.json").read_text(encoding="utf-8"))
    return f"{job['title']} at {job['company']}\n\n{job['description']}"


def test_retrieve_relevant_chunks_for_focused_query():
    structured_data = json.loads((FIXTURE_DIR / "profile.json").read_text(encoding="utf-8"))
    chunks = chunk_resume(structured_data)
    embedder = DeterministicEmbeddingProvider()

    results = retrieve_chunks("Python FastAPI PostgreSQL", chunks, embedder, top_k=5)
    retrieved_ids = {item.chunk.id for item in results}

    assert "skill-0" in retrieved_ids  # Python
    assert "skill-1" in retrieved_ids  # FastAPI (skill line beats long bullet for token overlap)
    assert "skill-2" in retrieved_ids  # PostgreSQL
    assert results[0].score >= results[-1].score


def test_retrieve_experience_bullet_for_specific_phrase():
    structured_data = json.loads((FIXTURE_DIR / "profile.json").read_text(encoding="utf-8"))
    chunks = chunk_resume(structured_data)
    embedder = DeterministicEmbeddingProvider()

    results = retrieve_chunks("FastAPI microservices migration", chunks, embedder, top_k=3)
    retrieved_ids = {item.chunk.id for item in results}

    assert "exp-0-hl-1" in retrieved_ids


def test_retrieve_full_job_description():
    structured_data = json.loads((FIXTURE_DIR / "profile.json").read_text(encoding="utf-8"))
    chunks = chunk_resume(structured_data)
    embedder = DeterministicEmbeddingProvider()

    results = retrieve_chunks(_load_job_query(), chunks, embedder, top_k=10)

    assert len(results) == 10
    assert results[0].score >= results[-1].score
    assert any("Python" in item.chunk.text or "FastAPI" in item.chunk.text for item in results)


def test_retrieve_respects_top_k():
    structured_data = json.loads((FIXTURE_DIR / "profile.json").read_text(encoding="utf-8"))
    chunks = chunk_resume(structured_data)
    embedder = DeterministicEmbeddingProvider()

    results = retrieve_chunks("Python FastAPI PostgreSQL", chunks, embedder, top_k=3)

    assert len(results) == 3


def test_retrieve_empty_chunks():
    embedder = DeterministicEmbeddingProvider()
    assert retrieve_chunks("Python", [], embedder) == []
