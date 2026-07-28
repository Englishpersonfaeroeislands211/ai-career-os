from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.cover_letter import CoverLetterCritique, CoverLetterDraft, CoverLetterResult
from app.schemas.match_analysis import MatchGap, MatchResult, MatchStrength
from app.services.cover_letter_generator import generate_cover_letter


@pytest.mark.asyncio
async def test_generate_cover_letter_runs_draft_critique_revise_chain():
    profile = SimpleNamespace(structured_data={"name": "Jane"}, resume_text="Jane")
    job = SimpleNamespace(
        title="Engineer",
        company="Acme",
        description="Python backend",
        location=None,
    )
    match_result = MatchResult(
        score=85.0,
        recommendation="apply",
        strengths=[MatchStrength(point=9.0, evidence="Python experience.")],
        gaps=[MatchGap(point=4.0, severity="low", evidence="No AWS listed.")],
        summary="Strong match.",
    )

    draft = CoverLetterDraft(
        body="Dear Acme,\n\nI am excited to apply.",
        tone="professional",
        highlights_used=["Python experience"],
    )
    critique = CoverLetterCritique(
        unsupported_claims=[],
        missing_strengths=["FastAPI migration"],
        tone_issues=[],
        revision_notes="Mention FastAPI migration.",
    )
    final = CoverLetterResult(
        body="Dear Acme,\n\nI am excited to apply with FastAPI experience.",
        tone="professional",
        highlights_used=["Python experience", "FastAPI migration"],
        critique_summary="Added missing FastAPI strength.",
    )

    mock_client = AsyncMock()
    mock_client.generate_structured = AsyncMock(side_effect=[draft, critique, final])

    with patch(
        "app.services.cover_letter_generator.get_llm_client",
        new=AsyncMock(return_value=mock_client),
    ):
        result = await generate_cover_letter(
            db=None,
            profile=profile,
            job=job,
            match_result=match_result,
        )

    assert mock_client.generate_structured.await_count == 3
    assert "FastAPI" in result.body
    assert result.critique_summary == "Added missing FastAPI strength."
