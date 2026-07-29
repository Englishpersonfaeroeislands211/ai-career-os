import json
from pathlib import Path

from app.services.rag import chunk_resume

FIXTURE_PROFILE = (
    Path(__file__).parent
    / "evals"
    / "fixtures"
    / "match"
    / "senior_python_backend"
    / "profile.json"
)


def test_chunk_structured_resume_from_fixture():
    structured_data = json.loads(FIXTURE_PROFILE.read_text(encoding="utf-8"))
    chunks = chunk_resume(structured_data)

    assert len(chunks) >= 10
    assert chunks[0].section == "headline"
    assert any(chunk.section == "skill" and chunk.text == "Python" for chunk in chunks)
    assert any(
        chunk.id == "exp-0-hl-1" and "FastAPI" in chunk.text and chunk.company == "Acme Corp"
        for chunk in chunks
    )


def test_chunk_plain_resume_splits_paragraphs():
    resume_text = "Senior engineer with Python experience.\n\nBuilt APIs at Acme Corp."

    chunks = chunk_resume(None, resume_text=resume_text)

    assert len(chunks) == 2
    assert chunks[0].section == "resume_text"
    assert chunks[0].text == "Senior engineer with Python experience."
    assert chunks[1].text == "Built APIs at Acme Corp."


def test_chunk_resume_empty_profile():
    assert chunk_resume(None, resume_text="   ") == []
