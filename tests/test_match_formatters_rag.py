import json
from pathlib import Path

import pytest

from app.services.match.formatters import build_match_user_message
from app.services.rag import DeterministicEmbeddingProvider

FIXTURE_DIR = Path(__file__).parent / "evals" / "fixtures" / "match" / "senior_python_backend"


def _fixture_profile():
    structured_data = json.loads((FIXTURE_DIR / "profile.json").read_text(encoding="utf-8"))
    from types import SimpleNamespace

    return SimpleNamespace(
        structured_data=structured_data,
        resume_text="Jane Doe resume text",
    )


def _fixture_job():
    job = json.loads((FIXTURE_DIR / "job.json").read_text(encoding="utf-8"))
    from types import SimpleNamespace

    return SimpleNamespace(
        title=job["title"],
        company=job["company"],
        description=job["description"],
        location=None,
        raw_metadata={"requirements": ["Python", "FastAPI", "PostgreSQL"]},
    )


@pytest.mark.asyncio
async def test_build_match_user_message_with_rag():
    message = await build_match_user_message(
        None,
        _fixture_profile(),
        _fixture_job(),
        use_rag=True,
        embedder=DeterministicEmbeddingProvider(),
        top_k=5,
    )

    assert "Retrieved resume evidence" in message
    assert "Python" in message
    assert "[id:" in message
    assert "Job description:" in message
    assert "Senior Backend Engineer" in message
    assert "Structured resume:" not in message


@pytest.mark.asyncio
async def test_build_match_user_message_without_rag():
    message = await build_match_user_message(
        None,
        _fixture_profile(),
        _fixture_job(),
        use_rag=False,
    )

    assert "Structured resume:" in message
    assert "Retrieved resume evidence" not in message
    assert '"name": "Jane Doe"' in message
