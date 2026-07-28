from uuid import uuid4

from app.models import Job
from app.services.screening_card import attach_screening_card_to_metadata, build_screening_card


def test_build_screening_card_uses_match_summary():
    job_id = uuid4()
    job = Job(
        id=job_id,
        title="Backend Engineer",
        company="Acme",
        description="Very long description " * 50,
        location="Remote · Berlin",
        raw_metadata={
            "match_summary": "Python backend role at a fintech.",
            "requirements": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Kubernetes"],
        },
    )

    card = build_screening_card(job)

    assert card.job_id == job_id
    assert card.summary == "Python backend role at a fintech."
    assert card.top_requirements == ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
    assert card.location == "Remote · Berlin"


def test_build_screening_card_falls_back_to_description():
    job = Job(
        id=uuid4(),
        title="Backend Engineer",
        company="Acme",
        description="Short backend role description.",
        raw_metadata={"requirements": []},
    )

    card = build_screening_card(job)

    assert card.summary == "Short backend role description."


def test_attach_screening_card_to_metadata():
    job = Job(
        id=uuid4(),
        title="Backend Engineer",
        company="Acme",
        description="Build APIs.",
        raw_metadata={
            "match_summary": "API backend role.",
            "requirements": ["Python"],
        },
    )

    metadata = attach_screening_card_to_metadata(job.raw_metadata, job)

    assert metadata["match_summary"] == "API backend role."
    assert metadata["screening_card"]["summary"] == "API backend role."
    assert metadata["screening_card"]["top_requirements"] == ["Python"]
