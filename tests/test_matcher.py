from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models import Job, MatchAnalysis, Profile
from app.schemas.match_analysis import MatchGap, MatchResult, MatchStrength
from app.services.llm.base import LLMConfigurationError
from app.services.match import analyze_match, run_match_analysis


@pytest.mark.asyncio
async def test_analyze_match_calls_llm_client():
    result = MatchResult(
        score=85.0,
        recommendation="apply",
        strengths=[MatchStrength(point=9.0, evidence="Strong Python experience.")],
        gaps=[MatchGap(point=4.0, severity="low", evidence="No AWS listed.")],
        summary="Strong match.",
    )
    mock_client = AsyncMock()
    mock_client.generate_structured.return_value = result

    profile = SimpleNamespace(structured_data={"name": "Jane"}, resume_text="Jane")
    job = SimpleNamespace(
        title="Backend Engineer",
        company="Acme",
        description="Python required",
        location=None,
        raw_metadata={},
    )

    with patch(
        "app.services.match.analyzer.get_llm_client",
        new=AsyncMock(return_value=mock_client),
    ):
        output, rag_chunks = await analyze_match(db=None, profile=profile, job=job)

    assert output.score == 85.0
    assert isinstance(rag_chunks, list)
    mock_client.generate_structured.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_match_propagates_configuration_error():
    with patch(
        "app.services.match.analyzer.get_llm_client",
        new=AsyncMock(side_effect=LLMConfigurationError("not configured")),
    ):
        with pytest.raises(LLMConfigurationError, match="not configured"):
            await analyze_match(
                db=None,
                profile=SimpleNamespace(structured_data=None, resume_text="Resume"),
                job=SimpleNamespace(
                    title="Role",
                    company="Co",
                    description="Desc",
                    location=None,
                    raw_metadata={},
                ),
            )


@pytest.mark.asyncio
async def test_run_match_analysis_marks_completed():
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
        title="Backend Engineer",
        company="Acme",
        description="Python role",
    )
    match_result = MatchResult(
        score=82.0,
        recommendation="apply",
        strengths=[MatchStrength(point=8.0, evidence="Python experience.")],
        gaps=[],
        summary="Good fit.",
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
            "app.services.match.orchestrator.analyze_match",
            new=AsyncMock(return_value=(match_result, [])),
        ),
    ):
        await run_match_analysis(analysis_id)

    assert analysis.status == "completed"
    assert analysis.result["depth"] == "full"
    assert analysis.result["score"] == match_result.model_dump()["score"]
    mock_session.commit.assert_awaited_once()
