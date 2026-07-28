from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.match_analysis import (
    BatchMatchResult,
    BatchScreeningResult,
    JobMatchResult,
    MatchGap,
    MatchResult,
    MatchStrength,
    ScreeningJobMatchResult,
)
from app.services.llm.base import LLMConfigurationError
from app.services.matcher import (
    analyze_match,
    analyze_matches_batch,
    run_batch_match_analysis,
    run_cascade_match_analysis,
    run_match_analysis,
)


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
    )

    with patch(
        "app.services.matcher.get_llm_client",
        new=AsyncMock(return_value=mock_client),
    ):
        output = await analyze_match(db=None, profile=profile, job=job)

    assert output.score == 85.0
    mock_client.generate_structured.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_match_propagates_configuration_error():
    with patch(
        "app.services.matcher.get_llm_client",
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
                ),
            )


@pytest.mark.asyncio
async def test_run_match_analysis_marks_completed():
    from uuid import uuid4

    from app.models import Job, MatchAnalysis, Profile

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
        patch("app.services.matcher.async_session", return_value=mock_context),
        patch(
            "app.services.matcher.analyze_match",
            new=AsyncMock(return_value=match_result),
        ),
    ):
        await run_match_analysis(analysis_id)

    assert analysis.status == "completed"
    assert analysis.result["depth"] == "full"
    assert analysis.result["score"] == match_result.model_dump()["score"]
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_matches_batch_uses_batch_prompt():
    from uuid import uuid4

    job_id = uuid4()
    batch_result = BatchMatchResult(
        matches=[
            JobMatchResult(
                job_id=job_id,
                score=80.0,
                recommendation="apply",
                strengths=[MatchStrength(point=8.0, evidence="Python.")],
                gaps=[MatchGap(point=3.0, severity="low", evidence="No Go.")],
                summary="Good fit.",
            )
        ]
    )
    mock_client = AsyncMock()
    mock_client.generate_structured.return_value = batch_result

    profile = SimpleNamespace(structured_data={"name": "Jane"}, resume_text="Jane")
    job = SimpleNamespace(
        id=job_id,
        title="Backend Engineer",
        company="Acme",
        description="Python required",
        location=None,
    )

    with patch(
        "app.services.matcher.get_llm_client",
        new=AsyncMock(return_value=mock_client),
    ):
        output = await analyze_matches_batch(db=None, profile=profile, jobs=[job])

    assert len(output.matches) == 1
    call_kwargs = mock_client.generate_structured.await_args.kwargs
    assert call_kwargs["response_model"] is BatchMatchResult
    assert "job_id:" in call_kwargs["messages"][1].content


@pytest.mark.asyncio
async def test_run_batch_match_analysis_updates_all_pending():
    from uuid import uuid4

    from app.models import Job, MatchAnalysis, Profile

    profile_id = uuid4()
    job_a_id = uuid4()
    job_b_id = uuid4()
    analysis_a_id = uuid4()
    analysis_b_id = uuid4()

    profile = Profile(
        id=profile_id,
        name="Jane",
        resume_text="Resume",
        structured_data={"name": "Jane"},
    )
    job_a = Job(id=job_a_id, title="A", company="Co", description="Python A")
    job_b = Job(id=job_b_id, title="B", company="Co", description="Python B")
    analysis_a = MatchAnalysis(
        id=analysis_a_id,
        profile_id=profile_id,
        job_id=job_a_id,
        status="pending",
    )
    analysis_b = MatchAnalysis(
        id=analysis_b_id,
        profile_id=profile_id,
        job_id=job_b_id,
        status="pending",
    )
    batch_result = BatchMatchResult(
        matches=[
            JobMatchResult(
                job_id=job_a_id,
                score=90.0,
                recommendation="apply",
                strengths=[],
                gaps=[],
                summary="Great fit A.",
            ),
            JobMatchResult(
                job_id=job_b_id,
                score=60.0,
                recommendation="maybe apply",
                strengths=[],
                gaps=[],
                summary="Moderate fit B.",
            ),
        ]
    )

    mock_session = AsyncMock()

    async def get_side_effect(model, obj_id):
        mapping = {
            analysis_a_id: analysis_a,
            analysis_b_id: analysis_b,
            profile_id: profile,
        }
        return mapping.get(obj_id)

    mock_session.get.side_effect = get_side_effect

    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job_a, job_b]
    mock_session.execute = AsyncMock(return_value=jobs_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None

    with (
        patch("app.services.matcher.async_session", return_value=mock_context),
        patch(
            "app.services.matcher.analyze_matches_batch",
            new=AsyncMock(return_value=batch_result),
        ),
    ):
        await run_batch_match_analysis([analysis_a_id, analysis_b_id])

    assert analysis_a.status == "completed"
    assert analysis_b.status == "completed"
    assert analysis_a.result["depth"] == "full"
    assert analysis_a.result["score"] == 90.0
    assert analysis_b.result["score"] == 60.0
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_cascade_match_analysis_screens_all_and_deepens_top_job():
    from uuid import uuid4

    from app.models import Job, MatchAnalysis, Profile

    profile_id = uuid4()
    job_a_id = uuid4()
    job_b_id = uuid4()
    analysis_a_id = uuid4()
    analysis_b_id = uuid4()

    profile = Profile(id=profile_id, name="Jane", resume_text="Resume", structured_data={})
    job_a = Job(id=job_a_id, title="A", company="Co", description="Python A")
    job_b = Job(id=job_b_id, title="B", company="Co", description="Python B")
    analysis_a = MatchAnalysis(
        id=analysis_a_id,
        profile_id=profile_id,
        job_id=job_a_id,
        status="pending",
    )
    analysis_b = MatchAnalysis(
        id=analysis_b_id,
        profile_id=profile_id,
        job_id=job_b_id,
        status="pending",
    )
    screen_result = BatchScreeningResult(
        matches=[
            ScreeningJobMatchResult(
                job_id=job_a_id,
                score=90.0,
                recommendation="apply",
                reason="Strong Python fit.",
            ),
            ScreeningJobMatchResult(
                job_id=job_b_id,
                score=55.0,
                recommendation="maybe apply",
                reason="Partial overlap.",
            ),
        ]
    )
    full_result = MatchResult(
        score=92.0,
        recommendation="apply",
        strengths=[],
        gaps=[],
        summary="Deep analysis for A.",
    )

    mock_session = AsyncMock()

    async def get_side_effect(model, obj_id):
        return {
            analysis_a_id: analysis_a,
            analysis_b_id: analysis_b,
            profile_id: profile,
        }.get(obj_id)

    mock_session.get.side_effect = get_side_effect
    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job_a, job_b]
    mock_session.execute = AsyncMock(return_value=jobs_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None

    with (
        patch("app.services.matcher.async_session", return_value=mock_context),
        patch(
            "app.services.matcher.analyze_matches_screen",
            new=AsyncMock(return_value=screen_result),
        ),
        patch(
            "app.services.matcher.analyze_match",
            new=AsyncMock(return_value=full_result),
        ) as mock_deep,
    ):
        await run_cascade_match_analysis([analysis_a_id, analysis_b_id], deep_analyze_top_k=1)

    assert analysis_a.result["depth"] == "full"
    assert analysis_a.result["score"] == 92.0
    assert analysis_b.result["depth"] == "screen"
    assert analysis_b.result["score"] == 55.0
    mock_deep.assert_awaited_once()
