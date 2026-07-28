from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas import JobRead
from app.schemas.company_research import (
    CompanyBrief,
    CompanyBriefContent,
    ResearchPlan,
    SearchResult,
)
from app.services.company_research import (
    build_research_plan_user_message,
    build_research_synthesize_user_message,
    company_brief_to_storage,
    research_company,
)


@pytest.mark.asyncio
async def test_research_company_runs_plan_search_synthesize():
    job = SimpleNamespace(
        title="Senior Backend Engineer",
        company="FinTech Labs",
        description="Python payment APIs at scale.",
        location="Remote",
        url="https://example.com/jobs/1",
    )
    plan = ResearchPlan(
        queries=[
            "FinTech Labs engineering culture",
            "FinTech Labs recent news",
        ]
    )
    search_results = [
        SearchResult(
            title="FinTech Labs launches new payments API",
            url="https://news.example/fintech-api",
            snippet="FinTech Labs announced a new developer API for payment processing.",
        ),
        SearchResult(
            title="Working at FinTech Labs - engineering blog",
            url="https://blog.example/fintech-culture",
            snippet="Remote-first team building payment infrastructure with Python.",
        ),
    ]
    brief_content = CompanyBriefContent(
        company="FinTech Labs",
        summary="FinTech Labs builds payment APIs with a remote Python-focused engineering team.",
        culture_signals=["Remote-first engineering"],
        recent_news=["Launched new payments API"],
        interview_signals=["Prepare payment system design topics"],
        red_flags=[],
    )

    mock_llm = AsyncMock()
    mock_llm.generate_structured = AsyncMock(side_effect=[plan, brief_content])

    mock_search = AsyncMock()
    mock_search.search = AsyncMock(
        side_effect=[
            search_results[:1],
            search_results[1:],
        ]
    )

    with patch(
        "app.services.company_research.get_llm_client",
        new=AsyncMock(return_value=mock_llm),
    ):
        result = await research_company(
            db=None,
            job=job,
            search_client=mock_search,
        )

    assert mock_llm.generate_structured.await_count == 2
    assert mock_search.search.await_count == 2
    assert result.company == "FinTech Labs"
    assert len(result.sources) == 2
    assert result.researched_at is not None
    assert "payment" in result.summary.casefold()


def test_build_research_messages_include_job_and_results():
    job = SimpleNamespace(
        title="Engineer",
        company="Acme",
        description="Build APIs",
        location=None,
        url=None,
    )
    results = [
        SearchResult(
            title="Acme news",
            url="https://example.com/acme",
            snippet="Acme expanded engineering.",
        )
    ]

    plan_message = build_research_plan_user_message(job)
    assert "Acme" in plan_message
    assert "Build APIs" in plan_message

    synth_message = build_research_synthesize_user_message(job, results)
    assert "Acme news" in synth_message
    assert "https://example.com/acme" in synth_message


def test_company_brief_storage_round_trips_through_job_read():
    researched_at = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
    brief = CompanyBrief(
        company="FinTech Labs",
        summary="Payment API company with remote Python team.",
        culture_signals=["Remote-first"],
        recent_news=["Launched developer API"],
        interview_signals=["System design for payments"],
        red_flags=[],
        sources=[
            SearchResult(
                title="FinTech Labs API launch",
                url="https://example.com/news",
                snippet="New payments API for developers.",
            )
        ],
        researched_at=researched_at,
    )

    job_read = JobRead.model_validate(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "title": "Engineer",
            "company": "FinTech Labs",
            "description": "Build APIs",
            "location": None,
            "url": None,
            "source": None,
            "raw_metadata": None,
            "company_brief": company_brief_to_storage(brief),
            "created_at": researched_at,
            "updated_at": researched_at,
        }
    )

    assert job_read.company_brief is not None
    assert job_read.company_brief.summary == brief.summary
    assert len(job_read.company_brief.sources) == 1
