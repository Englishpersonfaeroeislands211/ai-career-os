from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models import Job, MatchAnalysis, Profile
from app.schemas.match_analysis import (
    BatchScreeningResult,
    MatchGap,
    MatchResult,
    MatchStrength,
    ScreeningJobMatchResult,
)
from app.services.match import run_progressive_match_analysis


@pytest.mark.asyncio
async def test_run_progressive_match_analysis_screens_then_completes_full():
    analysis_id = uuid4()
    profile_id = uuid4()
    job_id = uuid4()

    analysis = MatchAnalysis(
        id=analysis_id,
        profile_id=profile_id,
        job_id=job_id,
        status="pending",
    )
    profile = Profile(
        id=profile_id,
        name="Jane Doe",
        resume_text="Jane Doe resume",
        structured_data={"name": "Jane Doe"},
    )
    job = Job(
        id=job_id,
        title="Engineer",
        company="Acme",
        description="Python",
    )
    screen_match = ScreeningJobMatchResult(
        job_id=job_id,
        score=72.0,
        recommendation="maybe apply",
        reason="Decent Python overlap.",
    )
    full_result = MatchResult(
        score=85.0,
        recommendation="apply",
        strengths=[MatchStrength(point=9.0, evidence="Strong Python.")],
        gaps=[MatchGap(point=4.0, severity="low", evidence="No AWS listed.")],
        summary="Strong match.",
    )

    mock_session = AsyncMock()

    async def get_side_effect(model, obj_id):
        if model is MatchAnalysis and obj_id == analysis_id:
            return analysis
        if model is Profile and obj_id == profile_id:
            return profile
        if model is Job and obj_id == job_id:
            return job
        return None

    mock_session.get.side_effect = get_side_effect

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None

    with (
        patch("app.services.match.orchestrator.async_session", return_value=mock_context),
        patch(
            "app.services.match.orchestrator.analyze_matches_screen",
            new=AsyncMock(
                return_value=BatchScreeningResult(matches=[screen_match]),
            ),
        ),
        patch(
            "app.services.match.orchestrator.analyze_match",
            new=AsyncMock(return_value=full_result),
        ),
    ):
        await run_progressive_match_analysis(analysis_id)

    assert mock_session.commit.await_count >= 2
    assert analysis.status == "completed"
    assert analysis.result["depth"] == "full"
    assert analysis.result["score"] == 85.0
